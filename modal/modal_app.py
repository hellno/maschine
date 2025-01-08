import sys

import modal

app = modal.App("example-hello-world")

@app.function()
def f(i: int) -> int:
    """Square a number and print a message based on its parity.
    
    Args:
        i: The input number to process
        
    Returns:
        The square of the input number
    """
    if i % 2 == 0:
        print("hello", i)
    else:
        print("world", i, file=sys.stderr)

    return i * i

@app.local_entrypoint()
def main(num_iterations: int = 200):
    """Run the function in different modes and aggregate results.
    
    Args:
        num_iterations: Number of parallel iterations to run (default: 200)
    """
    # run the function locally
    print("Local result:", f.local(1000))

    # run the function remotely on Modal
    print("Remote result:", f.remote(1000))

    # run the function in parallel and remotely on Modal
    total = 0
    for ret in f.map(range(num_iterations)):
        total += ret

    print(f"Total from {num_iterations} parallel executions:", total)
