import os
import subprocess
from dataclasses import dataclass

@dataclass
class TestCase:
    in_path: str
    out_path: str

@dataclass
class Test:
    name: str
    ir_path: str
    cases: list[TestCase]

@dataclass
class TestResult:
    error: bool
    error_str: str
    correct: bool
    writes: int
    output: list[str]
    target_output: list[str]    

def discover_tests(testdir = "tests"):
    for path in os.listdir(testdir):
        name = path

        ins = []
        outs = []
        irs = []
        for f in os.listdir(os.path.join(testdir, path)):
            base, ext = os.path.splitext(f)
            if ext == ".in":
                ins.append(base)
            elif ext == ".out":
                outs.append(base)
            elif ext == ".ir":
                irs.append(f)

        if len(irs) != 1:
            print(f"Error: {path} has {len(irs)} ir files")
            continue
        ir_path = os.path.join(testdir, path, irs[0])
        
        cases = []
        while len(ins) > 0:
            curr = ins.pop(0)
            if curr not in outs:
                continue
            outs.remove(curr)
            cases.append(TestCase(os.path.join(testdir, path, f"{curr}.in"), os.path.join(testdir, path, f"{curr}.out")))

        yield Test(name, ir_path, cases)

def run_case(assembly_path, case):
    input_path = os.path.join("..", case.in_path)
    with open(input_path, "r") as input_file:
        result = subprocess.check_output(["spim", "-keepstats", "-f", assembly_path], 
                        stdin=input_file, stderr=subprocess.STDOUT)

    output_path = os.path.join("..", case.out_path)
    with open(output_path, "r") as output_file:
        expected = output_file.readlines()
        expected = [line.strip() for line in expected]

    parts = result.split(bytes("\n", "utf-8"))
    parts = [p.decode("utf-8") for p in parts]
    parts = parts[1:] # first line is "Loaded: ..."

    # if you don't print a newline, by default output won't go to newline
    # i.e output of function call would have line 21Stats:...
    adjusted = []
    for part in parts:
        if "Stats" in part and not part.startswith("Stats"):
            adjusted.append(part[:part.index("Stats")])
            adjusted.append(part[part.index("Stats"):])
        else:
            adjusted.append(part)
    parts = adjusted

    err = not any(['Stats' in part for part in parts])
    if err:
        error_srt = "\n".join(parts)
        return TestResult(True, error_srt, False, 0, [], [])
    output = parts[:-3]

    stats = parts[-2]
    writes = int(stats[stats.index("writes ") + 7:stats.index("#branches")])
    correct = output == expected
    return TestResult(False, "", correct, writes, output, expected)

def run_test(test):
    print(f"\nRunning test {test.name}")

    if not os.path.isdir("logs"):
        os.mkdir("logs")

    # chdir to src
    os.chdir("src")
    ir_in_path = os.path.join("..", test.ir_path)
    ir_out_path_greedy = os.path.join("..", "logs", f"{test.name}_greedy.s")
    ir_out_path_naive = os.path.join("..", "logs", f"{test.name}_naive.s")
    
    # remove old output files
    if os.path.exists(ir_out_path_greedy):
        os.remove(ir_out_path_greedy)
    if os.path.exists(ir_out_path_naive):
        os.remove(ir_out_path_naive)
    
    subprocess.call(["sh", "./run.sh", ir_in_path, ir_out_path_naive, "--naive"])
    if not os.path.exists(ir_out_path_naive):
        print(f"Error: {test.name} (naive) failed to compile")
        os.chdir("..")
        return

    subprocess.call(["sh", "./run.sh", ir_in_path, ir_out_path_greedy, "--greedy"])
    # if path doesn't exist after, we had an error
    if not os.path.exists(ir_out_path_greedy):
        print(f"Error: {test.name} (greedy) failed to compile")
        os.chdir("..")
        return
    
    log_path = os.path.join("..", "logs", f"{test.name}.log")
    with open(log_path, "w") as log_file:
        for case in test.cases:
            for arg in ["naive", "greedy"]:
                result = run_case(ir_out_path_naive if arg == "naive" else ir_out_path_greedy, case)
                if result.error:
                    print(f"Error: {case.in_path}, {arg}")
                    log_file.write(f"Error: {case.in_path}, {arg}")
                    log_file.write(result.error_str)
                elif result.correct:
                    print(f"Correct: {case.in_path}, {arg} ({result.writes} writes)")
                    log_file.write(f"Correct: {case.in_path}, {arg} ({result.writes} writes)\n")
                else:
                    print(f"Incorrect: {case.in_path}, {arg} ({result.writes} writes)")
                    log_file.write(f"Incorrect: {case.in_path}, {arg} ({result.writes} writes)\n")
                    log_file.write("Expected:\n")
                    for line in result.target_output:
                        log_file.write(line + "\n")
                    log_file.write("Got:\n")
                    for line in result.output:
                        log_file.write(line + "\n")

    # chdir back to root
    os.chdir("..")

if __name__ == "__main__":
    import argparse

    # argparse with one argument: -b or --build
    parser = argparse.ArgumentParser()
    parser.add_argument("-b", "--build", help="Build the project", action="store_true")
    args = parser.parse_args()

    if args.build:
        subprocess.call(["sh", "./src/build.sh"])
    tests = discover_tests()

    for test in tests:
        run_test(test)