# Condensed Modal Python Reference

> **Note**: This reference combines the key concepts into a more compact overview, with Python examples to illustrate usage. For deeper details or expansions on any class or method, see [Modal official documentation](https://modal.com/docs) or jump to the relevant sections below.

---

## Table of Contents

- [1. Overview](#1-overview)
- [2. App](#2-app)
- [3. Functions](#3-functions)
- [4. Classes (`Cls`)](#4-classes-cls)
- [5. Containers / Images](#5-containers--images)
- [6. Data Storage (Volumes, Dict, Queue, NFS)](#6-data-storage-volumes-dict-queue-nfs)
- [7. Secrets](#7-secrets)
- [8. Scheduling](#8-scheduling)
- [9. Web Endpoints](#9-web-endpoints)
- [10. GPU Usage](#10-gpu-usage)
- [11. Sandboxes](#11-sandboxes)
- [12. Miscellaneous & Utilities](#12-miscellaneous--utilities)

---

## 1. Overview

Modal is a Python package for building, configuring, and deploying serverless Python applications. An application is represented by an `App` object, which groups one or more functions, classes, volumes, etc. Typical steps:

1. **Create an App** (e.g., `app = modal.App()`).
2. **Decorate** Python functions or classes to register them on the App (e.g., `@app.function()`).
3. **Configure** container images, resource requests (CPU, GPU), storage, secrets, etc.
4. **Run** the app locally with `app.run()`, or **deploy** it so it can run serverless in the cloud.

**Quick example**:
```python
import modal

app = modal.App()

@app.function()
def hello(name: str):
    return f"Hello, {name}!"

if __name__ == "__main__":
    with app.run():
        result = hello.remote("World")
        print(result)  # prints: Hello, World!

	More info: App docs | Functions docs | Modal official docs

2. App

Definition: An App is your main grouping of Modal objects.
	•	Create it with modal.App().
	•	Register objects (functions, classes, volumes, secrets, schedules) on that app.
	•	app.run() launches it locally; modal run script.py also works.
	•	For dynamic usage, app.include(other_app) merges objects from another app.

Key code:

app = modal.App("my_app")

@app.function()
def ping():
    return "pong"

@app.local_entrypoint()
def entry():
    res = ping.remote()
    print(res)

	See official docs on App

3. Functions

Functions are serverless callables you create with @app.function(). They run inside containers (Images).
	•	Remote calls: .remote(...) or .spawn(...) to invoke in the cloud.
	•	Return results to Python or get them asynchronously.
	•	Map / starmap for parallel processing across multiple inputs.

Example:

@app.function(cpu=2, secrets=[modal.Secret.from_name("my-secret")])
def process_item(x):
    # Some CPU-intensive work
    return x ** 2

@app.local_entrypoint()
def run_it():
    # Run on multiple items
    data = [1, 2, 3, 4]
    results = list(process_item.map(data))
    print(results)  # [1, 4, 9, 16]

Retries:

from modal import Retries

@app.function(retries=Retries(max_retries=3, backoff_coefficient=2.0))
def flaky_operation():
    # ...
    pass

4. Classes (Cls)

Classes can be registered with @app.cls(). Methods in these classes become remote-callable if decorated with @modal.method(). This is especially useful for stateful or model-based logic.

@app.cls()
class MyModel:
    def __init__(self, param):
        self.param = param

    @modal.method()
    def predict(self, x):
        return x + self.param

# usage
model = MyModel("hello")  # local instance reference
prediction = model.predict.remote("some_data")

	Cls references

5. Containers / Images

Images define the container environment:
	•	Use modal.Image.debian_slim().pip_install("requests")
	•	Or modal.Image.from_registry("python:3.10-slim")
	•	Add local code or files with .add_local_dir(), .pip_install_from_requirements(), etc.

Example:

image = (modal.Image.debian_slim()
    .pip_install("numpy", "pandas")
    .apt_install("git")
    .env({"MY_ENV_VAR": "some_value"})
)

@app.function(image=image)
def do_stuff():
    import os
    import numpy as np
    print("Env:", os.environ["MY_ENV_VAR"])
    print("Random:", np.random.rand())

	Image doc references

6. Data Storage (Volumes, Dict, Queue, NFS)

Modal offers different in-cloud data primitives:

Volumes

Durable, read-write filesystem snapshots. Attach with volumes={"/root/data": my_vol} in a function config.
Commit changes with volume.commit() and reload them with volume.reload().

vol = modal.Volume.from_name("my-volume", create_if_missing=True)

@app.function(volumes={"/data": vol})
def write():
    with open("/data/file.txt", "w") as f:
        f.write("Hello")
    vol.commit()

@app.function(volumes={"/data": vol})
def read():
    vol.reload()
    with open("/data/file.txt", "r") as f:
        print(f.read())

	More info on Volumes

Dict

In-memory store for short-term key-value data. Expires after ~30 days inactivity.

cache = modal.Dict.from_name("my-dict", create_if_missing=True)
cache["foo"] = 123
print(cache["foo"])

Queue

FIFO queue with optional partitions.

q = modal.Queue.from_name("my-queue", create_if_missing=True)
q.put("task1")
item = q.get()  # -> "task1"

NetworkFileSystem

Shared, writable filesystem. Similar usage to volumes but more straightforward for ephemeral data sharing.

nfs = modal.NetworkFileSystem.from_name("my-nfs", create_if_missing=True)
nfs.write_file("/hello.txt", open("localfile.txt", "rb"))

7. Secrets

Securely store and inject environment variables into containers.

secret = modal.Secret.from_name("my-aws-secret")

@app.function(secrets=[secret])
def use_secret():
    import os
    print(os.environ["AWS_ACCESS_KEY_ID"])

	Secrets doc

8. Scheduling

Periodic or Cron schedules:

from modal import Period, Cron

@app.function(schedule=Period(days=1))
def daily_job():
    print("Runs daily")

@app.function(schedule=Cron("0 9 * * 1"))  # Mondays at 9:00
def weekly_job():
    print("Runs weekly")

	Schedules doc

9. Web Endpoints

Decorator-based approaches:

# Basic endpoint
@app.function()
@modal.web_endpoint(method="GET")
def simple_endpoint(request):
    return {"message": "Hello world!"}

ASGI / WSGI:

@app.function()
@modal.asgi_app()
def fastapi_app():
    from fastapi import FastAPI
    fa = FastAPI()

    @fa.get("/")
    def root():
        return {"status": "ok"}

    return fa

Or run your own server with @modal.web_server(port=8000).

10. GPU Usage

Specify GPU resources in function/class definitions. E.g. gpu="a10g", gpu="a100:2", or use classes:

from modal import GPU

@app.function(gpu=GPU.A10G(count=1))
def heavy_ml_task(data):
    # GPU code
    pass

	GPU doc references

11. Sandboxes

Long-running containers you can SSH into or run commands interactively:

sb = modal.Sandbox.create("sleep", "infinity")
# run additional commands in that container
proc = sb.exec("ls", "-l")
for line in proc.stdout:
    print(line)
sb.terminate()  # to stop

	Sandbox doc

12. Miscellaneous & Utilities
	•	current_input_id() / current_function_call_id(): retrieve the ID of the current function call.
	•	forward(port=...): forward a container port (TCP) to a public address (useful for debugging or custom protocols).
	•	Retries(max_retries=..., backoff_coefficient=...): define retry logic.
	•	enable_output(): show logs inline during development.
	•	@enter / @exit: lifecycle hooks for container start/stop.

Example (advanced debugging):

@app.function()
def debug():
    with modal.forward(8000, unencrypted=True) as tunnel:
        print("Public TCP address:", tunnel.tcp_socket)
        # Run a small local server or debug service here

For any advanced usage or more exhaustive docstrings, consult Modal official docs. This condensed reference aims to capture typical usage patterns, important configuration methods, and short code samples for quick copy-paste integration.

