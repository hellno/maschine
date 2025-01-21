* * *

# API Reference

This is the API reference for the [`modal`](https://pypi.org/project/modal/)
Python package, which allows you to run distributed applications on Modal.

The reference is intended to be limited to low-level descriptions of various
programmatic functionality. If you’re just getting started with Modal, we would
instead recommend looking at the [guide](https://modal.com/docs/guide) first
or to get started quickly with an [example](https://modal.com/docs/examples).

## Application construction

|  |  |
| --- | --- |
| [`App`](https://modal.com/docs/reference/modal.App) | The main unit of deployment for code on Modal |
| [`App.function`](https://modal.com/docs/reference/modal.App#function) | Decorator for registering a function with an App |
| [`App.cls`](https://modal.com/docs/reference/modal.App#cls) | Decorator for registering a class with an App |

## Serverless execution

|  |  |
| --- | --- |
| [`Function`](https://modal.com/docs/reference/modal.Function) | A serverless function backed by an autoscaling container pool |
| [`Cls`](https://modal.com/docs/reference/modal.Cls) | A serverless class supporting parameterization and lifecycle hooks |

## Extended Function configuration

### Class parameterization

|  |  |
| --- | --- |
| [`parameter`](https://modal.com/docs/reference/modal.parameter) | Used to define class parameters, akin to a Dataclass field |

### Lifecycle hooks

|  |  |
| --- | --- |
| [`enter`](https://modal.com/docs/reference/modal.enter) | Decorator for a method that will be executed during container startup |
| [`exit`](https://modal.com/docs/reference/modal.exit) | Decorator for a method that will be executed during container shutdown |
| [`method`](https://modal.com/docs/reference/modal.method) | Decorator for exposing a method as an invokable function |

### Web integrations

|  |  |
| --- | --- |
| [`web_endpoint`](https://modal.com/docs/reference/modal.web_endpoint) | Decorator for exposing a simple FastAPI-based endpoint |
| [`asgi_app`](https://modal.com/docs/reference/modal.asgi_app) | Decorator for functions that construct an ASGI web application |
| [`wsgi_app`](https://modal.com/docs/reference/modal.wsgi_app) | Decorator for functions that construct a WSGI web application |
| [`web_server`](https://modal.com/docs/reference/modal.web_server) | Decorator for functions that construct an HTTP web server |

### Function semantics

|  |  |
| --- | --- |
| [`batched`](https://modal.com/docs/reference/modal.batched) | Decorator that marks a function as receiving batched inputs |

### Scheduling

|  |  |
| --- | --- |
| [`Cron`](https://modal.com/docs/reference/modal.Cron) | A schedule that runs based on cron syntax |
| [`Period`](https://modal.com/docs/reference/modal.Period) | A schedule that runs at a fixed interval |

### Exception handling

|  |  |
| --- | --- |
| [`Retries`](https://modal.com/docs/reference/modal.Retries) | Function retry policy for input failures |

## Sandboxed execution

|  |  |
| --- | --- |
| [`Sandbox`](https://modal.com/docs/reference/modal.Sandbox) | An interface for restricted code execution |
| [`ContainerProcess`](https://modal.com/docs/reference/modal.ContainerProcess) | An object representing a sandboxed process |
| [`FileIO`](https://modal.com/docs/reference/modal.FileIO) | A handle for a file in the Sandbox filesystem |

## Container configuration

|  |  |
| --- | --- |
| [`Image`](https://modal.com/docs/reference/modal.Image) | An API for specifying container images |
| [`Secret`](https://modal.com/docs/reference/modal.Secret) | A pointer to secrets that will be exposed as environment variables |

## Data primitives

### Persistent storage

|  |  |
| --- | --- |
| [`Volume`](https://modal.com/docs/reference/modal.Volume) | Distributed storage supporting highly performant parallel reads |
| [`CloudBucketMount`](https://modal.com/docs/reference/modal.CloudBucketMount) | Storage backed by a third-party cloud bucket (S3, etc.) |
| [`NetworkFileSystem`](https://modal.com/docs/reference/modal.NetworkFileSystem) | Shared, writeable cloud storage (superseded by `modal.Volume`) |

### In-memory storage

|  |  |
| --- | --- |
| [`Dict`](https://modal.com/docs/reference/modal.Dict) | A distributed key-value store |
| [`Queue`](https://modal.com/docs/reference/modal.Queue) | A distributed FIFO queue |

## Networking

|  |  |
| --- | --- |
| [`Proxy`](https://modal.com/docs/reference/modal.Proxy) | An object that provides a static outbound IP address for containers |
| [`forward`](https://modal.com/docs/reference/modal.forward) | A context manager for publicly exposing a port from a container |

[API Reference](https://modal.com/docs/reference#api-reference) [Application construction](https://modal.com/docs/reference#application-construction) [Serverless execution](https://modal.com/docs/reference#serverless-execution) [Extended Function configuration](https://modal.com/docs/reference#extended-function-configuration) [Class parameterization](https://modal.com/docs/reference#class-parameterization) [Lifecycle hooks](https://modal.com/docs/reference#lifecycle-hooks) [Web integrations](https://modal.com/docs/reference#web-integrations) [Function semantics](https://modal.com/docs/reference#function-semantics) [Scheduling](https://modal.com/docs/reference#scheduling) [Exception handling](https://modal.com/docs/reference#exception-handling) [Sandboxed execution](https://modal.com/docs/reference#sandboxed-execution) [Container configuration](https://modal.com/docs/reference#container-configuration) [Data primitives](https://modal.com/docs/reference#data-primitives) [Persistent storage](https://modal.com/docs/reference#persistent-storage) [In-memory storage](https://modal.com/docs/reference#in-memory-storage) [Networking](https://modal.com/docs/reference#networking)

* * *

# modal.App

```
class App(object)
```

Copy

A Modal App is a group of functions and classes that are deployed together.

The app serves at least three purposes:

- A unit of deployment for functions and classes.
- Syncing of identities of (primarily) functions and classes across processes
(your local Python interpreter and every Modal container active in your application).
- Manage log collection for everything that happens inside your code.

**Registering functions with an app**

The most common way to explicitly register an Object with an app is through the
`@app.function()` decorator. It both registers the annotated function itself and
other passed objects, like schedules and secrets, with the app:

```
import modal

app = modal.App()

@app.function(
    secrets=[modal.Secret.from_name("some_secret")],
    schedule=modal.Period(days=1),
)
def foo():
    pass
```

Copy

In this example, the secret and schedule are registered with the app.

```
def __init__(
    self,
    name: Optional[str] = None,
    *,
    image: Optional[_Image] = None,  # default image for all functions (default is `modal.Image.debian_slim()`)
    mounts: Sequence[_Mount] = [],  # default mounts for all functions
    secrets: Sequence[_Secret] = [],  # default secrets for all functions
    volumes: dict[Union[str, PurePosixPath], _Volume] = {},  # default volumes for all functions
) -> None:
```

Copy

Construct a new app, optionally with default image, mounts, secrets, or volumes.

```
image = modal.Image.debian_slim().pip_install(...)
secret = modal.Secret.from_name("my-secret")
volume = modal.Volume.from_name("my-data")
app = modal.App(image=image, secrets=[secret], volumes={"/mnt/data": volume})
```

Copy

## name

```
@property
def name(self) -> Optional[str]:
```

Copy

The user-provided name of the App.

## is\_interactive

```
@property
def is_interactive(self) -> bool:
```

Copy

Whether the current app for the app is running in interactive mode.

## app\_id

```
@property
def app_id(self) -> Optional[str]:
```

Copy

Return the app\_id of a running or stopped app.

## description

```
@property
def description(self) -> Optional[str]:
```

Copy

The App’s `name`, if available, or a fallback descriptive identifier.

## lookup

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def lookup(
    name: str,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
) -> "_App":
```

Copy

Look up an App with a given name, creating a new App if necessary.

Note that Apps created through this method will be in a deployed state,
but they will not have any associated Functions or Classes. This method
is mainly useful for creating an App to associate with a Sandbox:

```
app = modal.App.lookup("my-app", create_if_missing=True)
modal.Sandbox.create("echo", "hi", app=app)
```

Copy

## set\_description

```
def set_description(self, description: str):
```

Copy

## image

```
@property
def image(self) -> _Image:
```

Copy

## run

```
@contextmanager
def run(
    self,
    client: Optional[_Client] = None,
    show_progress: Optional[bool] = None,
    detach: bool = False,
    interactive: bool = False,
    environment_name: Optional[str] = None,
) -> AsyncGenerator["_App", None]:
```

Copy

Context manager that runs an app on Modal.

Use this as the main entry point for your Modal application. All calls
to Modal functions should be made within the scope of this context
manager, and they will correspond to the current app.

**Example**

```
with app.run():
    some_modal_function.remote()
```

Copy

To enable output printing, use `modal.enable_output()`:

```
with modal.enable_output():
    with app.run():
        some_modal_function.remote()
```

Copy

Note that you cannot invoke this in global scope of a file where you have
Modal functions or Classes, since that would run the block when the function
or class is imported in your containers as well. If you want to run it as
your entrypoint, consider wrapping it:

```
if __name__ == "__main__":
    with app.run():
        some_modal_function.remote()
```

Copy

You can then run your script with:

```
python app_module.py
```

Copy

Note that this method used to return a separate “App” object. This is
no longer useful since you can use the app itself for access to all
objects. For backwards compatibility reasons, it returns the same app.

## registered\_functions

```
@property
def registered_functions(self) -> dict[str, _Function]:
```

Copy

All modal.Function objects registered on the app.

## registered\_classes

```
@property
def registered_classes(self) -> dict[str, _Cls]:
```

Copy

All modal.Cls objects registered on the app.

## registered\_entrypoints

```
@property
def registered_entrypoints(self) -> dict[str, _LocalEntrypoint]:
```

Copy

All local CLI entrypoints registered on the app.

## indexed\_objects

```
@property
def indexed_objects(self) -> dict[str, _Object]:
```

Copy

## registered\_web\_endpoints

```
@property
def registered_web_endpoints(self) -> list[str]:
```

Copy

Names of web endpoint (ie. webhook) functions registered on the app.

## local\_entrypoint

```
def local_entrypoint(
    self, _warn_parentheses_missing: Any = None, *, name: Optional[str] = None
) -> Callable[[Callable[..., Any]], _LocalEntrypoint]:
```

Copy

Decorate a function to be used as a CLI entrypoint for a Modal App.

These functions can be used to define code that runs locally to set up the app,
and act as an entrypoint to start Modal functions from. Note that regular
Modal functions can also be used as CLI entrypoints, but unlike `local_entrypoint`,
those functions are executed remotely directly.

**Example**

```
@app.local_entrypoint()
def main():
    some_modal_function.remote()
```

Copy

You can call the function using `modal run` directly from the CLI:

```
modal run app_module.py
```

Copy

Note that an explicit [`app.run()`](https://modal.com/docs/reference/modal.App#run) is not needed, as an
[app](https://modal.com/docs/guide/apps) is automatically created for you.

**Multiple Entrypoints**

If you have multiple `local_entrypoint` functions, you can qualify the name of your app and function:

```
modal run app_module.py::app.some_other_function
```

Copy

**Parsing Arguments**

If your entrypoint function take arguments with primitive types, `modal run` automatically parses them as
CLI options.
For example, the following function can be called with `modal run app_module.py --foo 1 --bar "hello"`:

```
@app.local_entrypoint()
def main(foo: int, bar: str):
    some_modal_function.call(foo, bar)
```

Copy

Currently, `str`, `int`, `float`, `bool`, and `datetime.datetime` are supported.
Use `modal run app_module.py --help` for more information on usage.

## function

```
def function(
    self,
    _warn_parentheses_missing: Any = None,
    *,
    image: Optional[_Image] = None,  # The image to run as the container for the function
    schedule: Optional[Schedule] = None,  # An optional Modal Schedule for the function
    secrets: Sequence[_Secret] = (),  # Optional Modal Secret objects with environment variables for the container
    gpu: Union[\
        GPU_T, list[GPU_T]\
    ] = None,  # GPU request as string ("any", "T4", ...), object (`modal.GPU.A100()`, ...), or a list of either
    serialized: bool = False,  # Whether to send the function over using cloudpickle.
    mounts: Sequence[_Mount] = (),  # Modal Mounts added to the container
    network_file_systems: dict[\
        Union[str, PurePosixPath], _NetworkFileSystem\
    ] = {},  # Mountpoints for Modal NetworkFileSystems
    volumes: dict[\
        Union[str, PurePosixPath], Union[_Volume, _CloudBucketMount]\
    ] = {},  # Mount points for Modal Volumes  CloudBucketMounts
    allow_cross_region_volumes: bool = False,  # Whether using network file systems from other regions is allowed.
    # Specify, in fractional CPU cores, how many CPU cores to request.
    # Or, pass (request, limit) to additionally specify a hard limit in fractional CPU cores.
    # CPU throttling will prevent a container from exceeding its specified limit.
    cpu: Optional[Union[float, tuple[float, float]]] = None,
    # Specify, in MiB, a memory request which is the minimum memory required.
    # Or, pass (request, limit) to additionally specify a hard limit in MiB.
    memory: Optional[Union[int, tuple[int, int]]] = None,
    ephemeral_disk: Optional[int] = None,  # Specify, in MiB, the ephemeral disk size for the Function.
    proxy: Optional[_Proxy] = None,  # Reference to a Modal Proxy to use in front of this function.
    retries: Optional[Union[int, Retries]] = None,  # Number of times to retry each input in case of failure.
    concurrency_limit: Optional[\
        int\
    ] = None,  # An optional maximum number of concurrent containers running the function (keep_warm sets minimum).
    allow_concurrent_inputs: Optional[int] = None,  # Number of inputs the container may fetch to run concurrently.
    container_idle_timeout: Optional[int] = None,  # Timeout for idle containers waiting for inputs to shut down.
    timeout: Optional[int] = None,  # Maximum execution time of the function in seconds.
    keep_warm: Optional[\
        int\
    ] = None,  # An optional minimum number of containers to always keep warm (use concurrency_limit for maximum).
    name: Optional[str] = None,  # Sets the Modal name of the function within the app
    is_generator: Optional[\
        bool\
    ] = None,  # Set this to True if it's a non-generator function returning a [sync/async] generator object
    cloud: Optional[str] = None,  # Cloud provider to run the function on. Possible values are aws, gcp, oci, auto.
    region: Optional[Union[str, Sequence[str]]] = None,  # Region or regions to run the function on.
    enable_memory_snapshot: bool = False,  # Enable memory checkpointing for faster cold starts.
    block_network: bool = False,  # Whether to block network access
    # Maximum number of inputs a container should handle before shutting down.
    # With `max_inputs = 1`, containers will be single-use.
    max_inputs: Optional[int] = None,
    i6pn: Optional[bool] = None,  # Whether to enable IPv6 container networking within the region.
    # Parameters below here are experimental. Use with caution!
    _experimental_scheduler_placement: Optional[\
        SchedulerPlacement\
    ] = None,  # Experimental controls over fine-grained scheduling (alpha).
    _experimental_buffer_containers: Optional[int] = None,  # Number of additional, idle containers to keep around.
    _experimental_proxy_ip: Optional[str] = None,  # IP address of proxy
    _experimental_custom_scaling_factor: Optional[float] = None,  # Custom scaling factor
) -> _FunctionDecoratorType:
```

Copy

Decorator to register a new Modal [Function](https://modal.com/docs/reference/modal.Function) with this App.

## cls

```
@typing_extensions.dataclass_transform(field_specifiers=(parameter,), kw_only_default=True)
def cls(
    self,
    _warn_parentheses_missing: Optional[bool] = None,
    *,
    image: Optional[_Image] = None,  # The image to run as the container for the function
    secrets: Sequence[_Secret] = (),  # Optional Modal Secret objects with environment variables for the container
    gpu: Union[\
        GPU_T, list[GPU_T]\
    ] = None,  # GPU request as string ("any", "T4", ...), object (`modal.GPU.A100()`, ...), or a list of either
    serialized: bool = False,  # Whether to send the function over using cloudpickle.
    mounts: Sequence[_Mount] = (),
    network_file_systems: dict[\
        Union[str, PurePosixPath], _NetworkFileSystem\
    ] = {},  # Mountpoints for Modal NetworkFileSystems
    volumes: dict[\
        Union[str, PurePosixPath], Union[_Volume, _CloudBucketMount]\
    ] = {},  # Mount points for Modal Volumes  CloudBucketMounts
    allow_cross_region_volumes: bool = False,  # Whether using network file systems from other regions is allowed.
    # Specify, in fractional CPU cores, how many CPU cores to request.
    # Or, pass (request, limit) to additionally specify a hard limit in fractional CPU cores.
    # CPU throttling will prevent a container from exceeding its specified limit.
    cpu: Optional[Union[float, tuple[float, float]]] = None,
    # Specify, in MiB, a memory request which is the minimum memory required.
    # Or, pass (request, limit) to additionally specify a hard limit in MiB.
    memory: Optional[Union[int, tuple[int, int]]] = None,
    ephemeral_disk: Optional[int] = None,  # Specify, in MiB, the ephemeral disk size for the Function.
    proxy: Optional[_Proxy] = None,  # Reference to a Modal Proxy to use in front of this function.
    retries: Optional[Union[int, Retries]] = None,  # Number of times to retry each input in case of failure.
    concurrency_limit: Optional[int] = None,  # Limit for max concurrent containers running the function.
    allow_concurrent_inputs: Optional[int] = None,  # Number of inputs the container may fetch to run concurrently.
    container_idle_timeout: Optional[int] = None,  # Timeout for idle containers waiting for inputs to shut down.
    timeout: Optional[int] = None,  # Maximum execution time of the function in seconds.
    keep_warm: Optional[int] = None,  # An optional number of containers to always keep warm.
    cloud: Optional[str] = None,  # Cloud provider to run the function on. Possible values are aws, gcp, oci, auto.
    region: Optional[Union[str, Sequence[str]]] = None,  # Region or regions to run the function on.
    enable_memory_snapshot: bool = False,  # Enable memory checkpointing for faster cold starts.
    block_network: bool = False,  # Whether to block network access
    # Limits the number of inputs a container handles before shutting down.
    # Use `max_inputs = 1` for single-use containers.
    max_inputs: Optional[int] = None,
    # Parameters below here are experimental. Use with caution!
    _experimental_scheduler_placement: Optional[\
        SchedulerPlacement\
    ] = None,  # Experimental controls over fine-grained scheduling (alpha).
    _experimental_buffer_containers: Optional[int] = None,  # Number of additional, idle containers to keep around.
    _experimental_proxy_ip: Optional[str] = None,  # IP address of proxy
    _experimental_custom_scaling_factor: Optional[float] = None,  # Custom scaling factor
) -> Callable[[CLS_T], CLS_T]:
```

Copy

Decorator to register a new Modal [Cls](https://modal.com/docs/reference/modal.Cls) with this App.

## include

```
def include(self, /, other_app: "_App"):
```

Copy

Include another App’s objects in this one.

Useful for splitting up Modal Apps across different self-contained files.

```
app_a = modal.App("a")
@app.function()
def foo():
    ...

app_b = modal.App("b")
@app.function()
def bar():
    ...

app_a.include(app_b)

@app_a.local_entrypoint()
def main():
    # use function declared on the included app
    bar.remote()
```

Copy

[modal.App](https://modal.com/docs/reference/modal.App#modalapp) [name](https://modal.com/docs/reference/modal.App#name) [is\_interactive](https://modal.com/docs/reference/modal.App#is_interactive) [app\_id](https://modal.com/docs/reference/modal.App#app_id) [description](https://modal.com/docs/reference/modal.App#description) [lookup](https://modal.com/docs/reference/modal.App#lookup) [set\_description](https://modal.com/docs/reference/modal.App#set_description) [image](https://modal.com/docs/reference/modal.App#image) [run](https://modal.com/docs/reference/modal.App#run) [registered\_functions](https://modal.com/docs/reference/modal.App#registered_functions) [registered\_classes](https://modal.com/docs/reference/modal.App#registered_classes) [registered\_entrypoints](https://modal.com/docs/reference/modal.App#registered_entrypoints) [indexed\_objects](https://modal.com/docs/reference/modal.App#indexed_objects) [registered\_web\_endpoints](https://modal.com/docs/reference/modal.App#registered_web_endpoints) [local\_entrypoint](https://modal.com/docs/reference/modal.App#local_entrypoint) [function](https://modal.com/docs/reference/modal.App#function) [cls](https://modal.com/docs/reference/modal.App#cls) [include](https://modal.com/docs/reference/modal.App#include)

* * *

# modal.Client

```
class Client(object)
```

Copy

## is\_closed

```
def is_closed(self) -> bool:
```

Copy

## hello

```
def hello(self):
```

Copy

Connect to server and retrieve version information; raise appropriate error for various failures.

## from\_credentials

```
@classmethod
def from_credentials(cls, token_id: str, token_secret: str) -> "_Client":
```

Copy

Constructor based on token credentials; useful for managing Modal on behalf of third-party users.

**Usage:**

```
client = modal.Client.from_credentials("my_token_id", "my_token_secret")

modal.Sandbox.create("echo", "hi", client=client, app=app)
```

Copy

[modal.Client](https://modal.com/docs/reference/modal.Client#modalclient) [is\_closed](https://modal.com/docs/reference/modal.Client#is_closed) [hello](https://modal.com/docs/reference/modal.Client#hello) [from\_credentials](https://modal.com/docs/reference/modal.Client#from_credentials)

* * *

# modal.CloudBucketMount

```
class CloudBucketMount(object)
```

Copy

Mounts a cloud bucket to your container. Currently supports AWS S3 buckets.

S3 buckets are mounted using [AWS S3 Mountpoint](https://github.com/awslabs/mountpoint-s3).
S3 mounts are optimized for reading large files sequentially. It does not support every file operation; consult
[the AWS S3 Mountpoint documentation](https://github.com/awslabs/mountpoint-s3/blob/main/doc/SEMANTICS.md)
for more information.

**AWS S3 Usage**

```
import subprocess

app = modal.App()
secret = modal.Secret.from_name(
    "aws-secret",
    required_keys=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
    # Note: providing AWS_REGION can help when automatic detection of the bucket region fails.
)

@app.function(
    volumes={
        "/my-mount": modal.CloudBucketMount(
            bucket_name="s3-bucket-name",
            secret=secret,
            read_only=True
        )
    }
)
def f():
    subprocess.run(["ls", "/my-mount"], check=True)
```

Copy

**Cloudflare R2 Usage**

Cloudflare R2 is [S3-compatible](https://developers.cloudflare.com/r2/api/s3/api/) so its setup looks
very similar to S3. But additionally the `bucket_endpoint_url` argument must be passed.

```
import subprocess

app = modal.App()
secret = modal.Secret.from_name(
    "r2-secret",
    required_keys=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY"]
)

@app.function(
    volumes={
        "/my-mount": modal.CloudBucketMount(
            bucket_name="my-r2-bucket",
            bucket_endpoint_url="https://.r2.cloudflarestorage.com",
            secret=secret,
            read_only=True
        )
    }
)
def f():
    subprocess.run(["ls", "/my-mount"], check=True)
```

Copy

**Google GCS Usage**

Google Cloud Storage (GCS) is [S3-compatible](https://cloud.google.com/storage/docs/interoperability).
GCS Buckets also require a secret with Google-specific key names (see below) populated with
a [HMAC key](https://cloud.google.com/storage/docs/authentication/managing-hmackeys#create).

```
import subprocess

app = modal.App()
gcp_hmac_secret = modal.Secret.from_name(
    "gcp-secret",
    required_keys=["GOOGLE_ACCESS_KEY_ID", "GOOGLE_ACCESS_KEY_SECRET"]
)

@app.function(
    volumes={
        "/my-mount": modal.CloudBucketMount(
            bucket_name="my-gcs-bucket",
            bucket_endpoint_url="https://storage.googleapis.com",
            secret=gcp_hmac_secret,
        )
    }
)
def f():
    subprocess.run(["ls", "/my-mount"], check=True)
```

Copy

```
def __init__(self, bucket_name: str, bucket_endpoint_url: Optional[str] = None, key_prefix: Optional[str] = None, secret: Optional[modal.secret._Secret] = None, oidc_auth_role_arn: Optional[str] = None, read_only: bool = False, requester_pays: bool = False) -> None
```

Copy

[modal.CloudBucketMount](https://modal.com/docs/reference/modal.CloudBucketMount#modalcloudbucketmount)

* * *

# modal.Cls

```
class Cls(modal.object.Object)
```

Copy

Cls adds method pooling and [lifecycle hook](https://modal.com/docs/guide/lifecycle-functions) behavior
to [modal.Function](https://modal.com/docs/reference/modal.Function).

Generally, you will not construct a Cls directly.
Instead, use the [`@app.cls()`](https://modal.com/docs/reference/modal.App#cls) decorator on the App object.

```
def __init__(self, *args, **kwargs):
```

Copy

## hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

## from\_name

```
@classmethod
@renamed_parameter((2024, 12, 18), "tag", "name")
def from_name(
    cls: type["_Cls"],
    app_name: str,
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    environment_name: Optional[str] = None,
    workspace: Optional[str] = None,
) -> "_Cls":
```

Copy

Reference a Cls from a deployed App by its name.

In contrast to `modal.Cls.lookup`, this is a lazy method
that defers hydrating the local object with metadata from
Modal servers until the first time it is actually used.

```
Model = modal.Cls.from_name("other-app", "Model")
```

Copy

## with\_options

```
def with_options(
    self: "_Cls",
    cpu: Optional[Union[float, tuple[float, float]]] = None,
    memory: Optional[Union[int, tuple[int, int]]] = None,
    gpu: GPU_T = None,
    secrets: Collection[_Secret] = (),
    volumes: dict[Union[str, os.PathLike], _Volume] = {},
    retries: Optional[Union[int, Retries]] = None,
    timeout: Optional[int] = None,
    concurrency_limit: Optional[int] = None,
    allow_concurrent_inputs: Optional[int] = None,
    container_idle_timeout: Optional[int] = None,
) -> "_Cls":
```

Copy

**Beta:** Allows for the runtime modification of a modal.Cls’s configuration.

This is a beta feature and may be unstable.

**Usage:**

```
Model = modal.Cls.lookup("my_app", "Model")
ModelUsingGPU = Model.with_options(gpu="A100")
ModelUsingGPU().generate.remote(42)  # will run with an A100 GPU
```

Copy

## lookup

```
@staticmethod
@renamed_parameter((2024, 12, 18), "tag", "name")
def lookup(
    app_name: str,
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    workspace: Optional[str] = None,
) -> "_Cls":
```

Copy

Lookup a Cls from a deployed App by its name.

In contrast to `modal.Cls.from_name`, this is an eager method
that will hydrate the local object with metadata from Modal servers.

```
Model = modal.Cls.lookup("other-app", "Model")
model = Model()
model.inference(...)
```

Copy

[modal.Cls](https://modal.com/docs/reference/modal.Cls#modalcls) [hydrate](https://modal.com/docs/reference/modal.Cls#hydrate) [from\_name](https://modal.com/docs/reference/modal.Cls#from_name) [with\_options](https://modal.com/docs/reference/modal.Cls#with_options) [lookup](https://modal.com/docs/reference/modal.Cls#lookup)

* * *

# modal.container\_process

## modal.container\_process.ContainerProcess

```
class ContainerProcess(typing.Generic)
```

Copy

```
def __init__(
    self,
    process_id: str,
    client: _Client,
    stdout: StreamType = StreamType.PIPE,
    stderr: StreamType = StreamType.PIPE,
    text: bool = True,
    by_line: bool = False,
) -> None:
```

Copy

### stdout

```
@property
def stdout(self) -> _StreamReader[T]:
```

Copy

StreamReader for the container process’s stdout stream.

### stderr

```
@property
def stderr(self) -> _StreamReader[T]:
```

Copy

StreamReader for the container process’s stderr stream.

### stdin

```
@property
def stdin(self) -> _StreamWriter:
```

Copy

StreamWriter for the container process’s stdin stream.

### returncode

```
@property
def returncode(self) -> int:
```

Copy

### poll

```
def poll(self) -> Optional[int]:
```

Copy

Check if the container process has finished running.

Returns `None` if the process is still running, else returns the exit code.

### wait

```
def wait(self) -> int:
```

Copy

Wait for the container process to finish running. Returns the exit code.

### attach

```
def attach(self, *, pty: Optional[bool] = None):
```

Copy

[modal.container\_process](https://modal.com/docs/reference/modal.ContainerProcess#modalcontainer_process) [modal.container\_process.ContainerProcess](https://modal.com/docs/reference/modal.ContainerProcess#modalcontainer_processcontainerprocess) [stdout](https://modal.com/docs/reference/modal.ContainerProcess#stdout) [stderr](https://modal.com/docs/reference/modal.ContainerProcess#stderr) [stdin](https://modal.com/docs/reference/modal.ContainerProcess#stdin) [returncode](https://modal.com/docs/reference/modal.ContainerProcess#returncode) [poll](https://modal.com/docs/reference/modal.ContainerProcess#poll) [wait](https://modal.com/docs/reference/modal.ContainerProcess#wait) [attach](https://modal.com/docs/reference/modal.ContainerProcess#attach)

* * *

# modal.Cron

```
class Cron(modal.schedule.Schedule)
```

Copy

Cron jobs are a type of schedule, specified using the
[Unix cron tab](https://crontab.guru/) syntax.

The alternative schedule type is the [`modal.Period`](https://modal.com/docs/reference/modal.Period).

**Usage**

```
import modal
app = modal.App()

@app.function(schedule=modal.Cron("* * * * *"))
def f():
    print("This function will run every minute")
```

Copy

We can specify different schedules with cron strings, for example:

```
modal.Cron("5 4 * * *")  # run at 4:05am every night
modal.Cron("0 9 * * 4")  # runs every Thursday 9am
```

Copy

```
def __init__(self, cron_string: str) -> None:
```

Copy

Construct a schedule that runs according to a cron expression string.

[modal.Cron](https://modal.com/docs/reference/modal.Cron#modalcron)

* * *

# modal.dict

## modal.dict.Dict

```
class Dict(modal.object.Object)
```

Copy

Distributed dictionary for storage in Modal apps.

Keys and values can be essentially any object, so long as they can be serialized by
`cloudpickle`, which includes other Modal objects.

**Lifetime of a Dict and its items**

An individual dict entry will expire 30 days after it was last added to its Dict object.
Additionally, data are stored in memory on the Modal server and could be lost due to
unexpected server restarts. Because of this, `Dict` is best suited for storing short-term
state and is not recommended for durable storage.

**Usage**

```
from modal import Dict

my_dict = Dict.from_name("my-persisted_dict", create_if_missing=True)

my_dict["some key"] = "some value"
my_dict[123] = 456

assert my_dict["some key"] == "some value"
assert my_dict[123] == 456
```

Copy

The `Dict` class offers a few methods for operations that are usually accomplished
in Python with operators, such as `Dict.put` and `Dict.contains`. The advantage of
these methods is that they can be safely called in an asynchronous context, whereas
their operator-based analogues will block the event loop.

For more examples, see the [guide](https://modal.com/docs/guide/dicts-and-queues#modal-dicts).

### hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

### ephemeral

```
@classmethod
@contextmanager
def ephemeral(
    cls: type["_Dict"],
    data: Optional[dict] = None,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    _heartbeat_sleep: float = EPHEMERAL_OBJECT_HEARTBEAT_SLEEP,
) -> Iterator["_Dict"]:
```

Copy

Creates a new ephemeral dict within a context manager:

Usage:

```
from modal import Dict

with Dict.ephemeral() as d:
    d["foo"] = "bar"
```

Copy

```
async with Dict.ephemeral() as d:
    await d.put.aio("foo", "bar")
```

Copy

### from\_name

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def from_name(
    name: str,
    data: Optional[dict] = None,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
) -> "_Dict":
```

Copy

Reference a named Dict, creating if necessary.

In contrast to `modal.Dict.lookup`, this is a lazy method
that defers hydrating the local object with metadata from
Modal servers until the first time it is actually used.

```
d = modal.Dict.from_name("my-dict", create_if_missing=True)
d[123] = 456
```

Copy

### lookup

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def lookup(
    name: str,
    data: Optional[dict] = None,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
) -> "_Dict":
```

Copy

Lookup a named Dict.

In contrast to `modal.Dict.from_name`, this is an eager method
that will hydrate the local object with metadata from Modal servers.

```
d = modal.Dict.lookup("my-dict")
d["xyz"] = 123
```

Copy

### delete

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def delete(
    name: str,
    *,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
):
```

Copy

### clear

```
@live_method
def clear(self) -> None:
```

Copy

Remove all items from the Dict.

### get

```
@live_method
def get(self, key: Any, default: Optional[Any] = None) -> Any:
```

Copy

Get the value associated with a key.

Returns `default` if key does not exist.

### contains

```
@live_method
def contains(self, key: Any) -> bool:
```

Copy

Return if a key is present.

### len

```
@live_method
def len(self) -> int:
```

Copy

Return the length of the dictionary, including any expired keys.

### update

```
@live_method
def update(self, **kwargs) -> None:
```

Copy

Update the dictionary with additional items.

### put

```
@live_method
def put(self, key: Any, value: Any) -> None:
```

Copy

Add a specific key-value pair to the dictionary.

### pop

```
@live_method
def pop(self, key: Any) -> Any:
```

Copy

Remove a key from the dictionary, returning the value if it exists.

### keys

```
@live_method_gen
def keys(self) -> Iterator[Any]:
```

Copy

Return an iterator over the keys in this dictionary.

Note that (unlike with Python dicts) the return value is a simple iterator,
and results are unordered.

### values

```
@live_method_gen
def values(self) -> Iterator[Any]:
```

Copy

Return an iterator over the values in this dictionary.

Note that (unlike with Python dicts) the return value is a simple iterator,
and results are unordered.

### items

```
@live_method_gen
def items(self) -> Iterator[tuple[Any, Any]]:
```

Copy

Return an iterator over the (key, value) tuples in this dictionary.

Note that (unlike with Python dicts) the return value is a simple iterator,
and results are unordered.

[modal.dict](https://modal.com/docs/reference/modal.Dict#modaldict) [modal.dict.Dict](https://modal.com/docs/reference/modal.Dict#modaldictdict) [hydrate](https://modal.com/docs/reference/modal.Dict#hydrate) [ephemeral](https://modal.com/docs/reference/modal.Dict#ephemeral) [from\_name](https://modal.com/docs/reference/modal.Dict#from_name) [lookup](https://modal.com/docs/reference/modal.Dict#lookup) [delete](https://modal.com/docs/reference/modal.Dict#delete) [clear](https://modal.com/docs/reference/modal.Dict#clear) [get](https://modal.com/docs/reference/modal.Dict#get) [contains](https://modal.com/docs/reference/modal.Dict#contains) [len](https://modal.com/docs/reference/modal.Dict#len) [update](https://modal.com/docs/reference/modal.Dict#update) [put](https://modal.com/docs/reference/modal.Dict#put) [pop](https://modal.com/docs/reference/modal.Dict#pop) [keys](https://modal.com/docs/reference/modal.Dict#keys) [values](https://modal.com/docs/reference/modal.Dict#values) [items](https://modal.com/docs/reference/modal.Dict#items)

* * *

# modal.Error

```
class Error(Exception)
```

Copy

Base class for all Modal errors. See [`modal.exception`](https://modal.com/docs/reference/modal.exception) for the specialized
error classes.

**Usage**

```
import modal

try:
    ...
except modal.Error:
    # Catch any exception raised by Modal's systems.
    print("Responding to error...")
```

Copy

[modal.Error](https://modal.com/docs/reference/modal.Error#modalerror)

* * *

# modal.file\_io

## modal.file\_io.FileIO

```
class FileIO(typing.Generic)
```

Copy

FileIO handle, used in the Sandbox filesystem API.

The API is designed to mimic Python’s io.FileIO.

**Usage**

```
import modal

app = modal.App.lookup("my-app", create_if_missing=True)

sb = modal.Sandbox.create(app=app)
f = sb.open("/tmp/foo.txt", "w")
f.write("hello")
f.close()
```

Copy

```
def __init__(self, client: _Client, task_id: str) -> None:
```

Copy

### create

```
@classmethod
def create(
    cls, path: str, mode: Union["_typeshed.OpenTextMode", "_typeshed.OpenBinaryMode"], client: _Client, task_id: str
) -> "_FileIO":
```

Copy

Create a new FileIO handle.

### read

```
def read(self, n: Optional[int] = None) -> T:
```

Copy

Read n bytes from the current position, or the entire remaining file if n is None.

### readline

```
def readline(self) -> T:
```

Copy

Read a single line from the current position.

### readlines

```
def readlines(self) -> Sequence[T]:
```

Copy

Read all lines from the current position.

### write

```
def write(self, data: Union[bytes, str]) -> None:
```

Copy

Write data to the current position.

Writes may not appear until the entire buffer is flushed, which
can be done manually with `flush()` or automatically when the file is
closed.

### flush

```
def flush(self) -> None:
```

Copy

Flush the buffer to disk.

### seek

```
def seek(self, offset: int, whence: int = 0) -> None:
```

Copy

Move to a new position in the file.

`whence` defaults to 0 (absolute file positioning); other values are 1
(relative to the current position) and 2 (relative to the file’s end).

### ls

```
@classmethod
def ls(cls, path: str, client: _Client, task_id: str) -> list[str]:
```

Copy

List the contents of the provided directory.

### mkdir

```
@classmethod
def mkdir(cls, path: str, client: _Client, task_id: str, parents: bool = False) -> None:
```

Copy

Create a new directory.

### rm

```
@classmethod
def rm(cls, path: str, client: _Client, task_id: str, recursive: bool = False) -> None:
```

Copy

Remove a file or directory in the Sandbox.

### watch

```
@classmethod
def watch(
    cls,
    path: str,
    client: _Client,
    task_id: str,
    filter: Optional[list[FileWatchEventType]] = None,
    recursive: bool = False,
    timeout: Optional[int] = None,
) -> Iterator[FileWatchEvent]:
```

Copy

### close

```
def close(self) -> None:
```

Copy

Flush the buffer and close the file.

## modal.file\_io.FileWatchEvent

```
class FileWatchEvent(object)
```

Copy

FileWatchEvent(paths: list\[str\], type: modal.file\_io.FileWatchEventType)

```
def __init__(self, paths: list[str], type: modal.file_io.FileWatchEventType) -> None
```

Copy

## modal.file\_io.FileWatchEventType

```
class FileWatchEventType(enum.Enum)
```

Copy

An enumeration.

The possible values are:

- `Unknown`
- `Access`
- `Create`
- `Modify`
- `Remove`

## modal.file\_io.delete\_bytes

```
async def delete_bytes(file: "_FileIO", start: Optional[int] = None, end: Optional[int] = None) -> None:
```

Copy

Delete a range of bytes from the file.

`start` and `end` are byte offsets. `start` is inclusive, `end` is exclusive.
If either is None, the start or end of the file is used, respectively.

## modal.file\_io.replace\_bytes

```
async def replace_bytes(file: "_FileIO", data: bytes, start: Optional[int] = None, end: Optional[int] = None) -> None:
```

Copy

Replace a range of bytes in the file with new data. The length of the data does not
have to be the same as the length of the range being replaced.

`start` and `end` are byte offsets. `start` is inclusive, `end` is exclusive.
If either is None, the start or end of the file is used, respectively.

[modal.file\_io](https://modal.com/docs/reference/modal.FileIO#modalfile_io) [modal.file\_io.FileIO](https://modal.com/docs/reference/modal.FileIO#modalfile_iofileio) [create](https://modal.com/docs/reference/modal.FileIO#create) [read](https://modal.com/docs/reference/modal.FileIO#read) [readline](https://modal.com/docs/reference/modal.FileIO#readline) [readlines](https://modal.com/docs/reference/modal.FileIO#readlines) [write](https://modal.com/docs/reference/modal.FileIO#write) [flush](https://modal.com/docs/reference/modal.FileIO#flush) [seek](https://modal.com/docs/reference/modal.FileIO#seek) [ls](https://modal.com/docs/reference/modal.FileIO#ls) [mkdir](https://modal.com/docs/reference/modal.FileIO#mkdir) [rm](https://modal.com/docs/reference/modal.FileIO#rm) [watch](https://modal.com/docs/reference/modal.FileIO#watch) [close](https://modal.com/docs/reference/modal.FileIO#close) [modal.file\_io.FileWatchEvent](https://modal.com/docs/reference/modal.FileIO#modalfile_iofilewatchevent) [modal.file\_io.FileWatchEventType](https://modal.com/docs/reference/modal.FileIO#modalfile_iofilewatcheventtype) [modal.file\_io.delete\_bytes](https://modal.com/docs/reference/modal.FileIO#modalfile_iodelete_bytes) [modal.file\_io.replace\_bytes](https://modal.com/docs/reference/modal.FileIO#modalfile_ioreplace_bytes)

* * *

# modal.FilePatternMatcher

```
class FilePatternMatcher(modal.file_pattern_matcher._AbstractPatternMatcher)
```

Copy

Allows matching file Path objects against a list of patterns.

**Usage:**

```
from pathlib import Path
from modal import FilePatternMatcher

matcher = FilePatternMatcher("*.py")

assert matcher(Path("foo.py"))

# You can also negate the matcher.
negated_matcher = ~matcher

assert not negated_matcher(Path("foo.py"))
```

Copy

```
def __init__(self, *pattern: str) -> None:
```

Copy

Initialize a new FilePatternMatcher instance.

Args:
pattern (str): One or more pattern strings.

Raises:
ValueError: If an illegal exclusion pattern is provided.

## from\_file

```
@classmethod
def from_file(cls, file_path: Union[str, Path]) -> "FilePatternMatcher":
```

Copy

Initialize a new FilePatternMatcher instance from a file.

The patterns in the file will be read lazily when the matcher is first used.

Args:
file\_path (Path): The path to the file containing patterns.

**Usage:**

```
from modal import FilePatternMatcher

matcher = FilePatternMatcher.from_file("/path/to/ignorefile")
```

Copy

[modal.FilePatternMatcher](https://modal.com/docs/reference/modal.FilePatternMatcher#modalfilepatternmatcher) [from\_file](https://modal.com/docs/reference/modal.FilePatternMatcher#from_file)

* * *

# modal.functions

## modal.functions.Function

```
class Function(typing.Generic, modal.object.Object)
```

Copy

Functions are the basic units of serverless execution on Modal.

Generally, you will not construct a `Function` directly. Instead, use the
`App.function()` decorator to register your Python functions with your App.

```
def __init__(self, *args, **kwargs):
```

Copy

### hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

### keep\_warm

```
@live_method
def keep_warm(self, warm_pool_size: int) -> None:
```

Copy

Set the warm pool size for the function.

Please exercise care when using this advanced feature!
Setting and forgetting a warm pool on functions can lead to increased costs.

```
# Usage on a regular function.
f = modal.Function.lookup("my-app", "function")
f.keep_warm(2)

# Usage on a parametrized function.
Model = modal.Cls.lookup("my-app", "Model")
Model("fine-tuned-model").keep_warm(2)
```

Copy

### from\_name

```
@classmethod
@renamed_parameter((2024, 12, 18), "tag", "name")
def from_name(
    cls: type["_Function"],
    app_name: str,
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    environment_name: Optional[str] = None,
) -> "_Function":
```

Copy

Reference a Function from a deployed App by its name.

In contast to `modal.Function.lookup`, this is a lazy method
that defers hydrating the local object with metadata from
Modal servers until the first time it is actually used.

```
f = modal.Function.from_name("other-app", "function")
```

Copy

### lookup

```
@staticmethod
@renamed_parameter((2024, 12, 18), "tag", "name")
def lookup(
    app_name: str,
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
) -> "_Function":
```

Copy

Lookup a Function from a deployed App by its name.

In contrast to `modal.Function.from_name`, this is an eager method
that will hydrate the local object with metadata from Modal servers.

```
f = modal.Function.lookup("other-app", "function")
```

Copy

### web\_url

```
@property
@live_method
def web_url(self) -> str:
```

Copy

URL of a Function running as a web endpoint.

### remote

```
@live_method
def remote(self, *args: P.args, **kwargs: P.kwargs) -> ReturnType:
```

Copy

Calls the function remotely, executing it with the given arguments and returning the execution’s result.

### remote\_gen

```
@live_method_gen
def remote_gen(self, *args, **kwargs) -> AsyncGenerator[Any, None]:
```

Copy

Calls the generator remotely, executing it with the given arguments and returning the execution’s result.

### local

```
def local(self, *args: P.args, **kwargs: P.kwargs) -> OriginalReturnType:
```

Copy

Calls the function locally, executing it with the given arguments and returning the execution’s result.

The function will execute in the same environment as the caller, just like calling the underlying function
directly in Python. In particular, only secrets available in the caller environment will be available
through environment variables.

### spawn

```
@live_method
def spawn(self, *args: P.args, **kwargs: P.kwargs) -> "_FunctionCall[ReturnType]":
```

Copy

Calls the function with the given arguments, without waiting for the results.

Returns a `modal.functions.FunctionCall` object, that can later be polled or
waited for using `.get(timeout=...)`.
Conceptually similar to `multiprocessing.pool.apply_async`, or a Future/Promise in other contexts.

### get\_raw\_f

```
def get_raw_f(self) -> Callable[..., Any]:
```

Copy

Return the inner Python object wrapped by this Modal Function.

### get\_current\_stats

```
@live_method
def get_current_stats(self) -> FunctionStats:
```

Copy

Return a `FunctionStats` object describing the current function’s queue and runner counts.

### map

```
@warn_if_generator_is_not_consumed(function_name="Function.map")
def map(
    self,
    *input_iterators: typing.Iterable[Any],  # one input iterator per argument in the mapped-over function/generator
    kwargs={},  # any extra keyword arguments for the function
    order_outputs: bool = True,  # return outputs in order
    return_exceptions: bool = False,  # propagate exceptions (False) or aggregate them in the results list (True)
) -> AsyncOrSyncIterable:
```

Copy

Parallel map over a set of inputs.

Takes one iterator argument per argument in the function being mapped over.

Example:

```
@app.function()
def my_func(a):
    return a ** 2

@app.local_entrypoint()
def main():
    assert list(my_func.map([1, 2, 3, 4])) == [1, 4, 9, 16]
```

Copy

If applied to a `stub.function`, `map()` returns one result per input and the output order
is guaranteed to be the same as the input order. Set `order_outputs=False` to return results
in the order that they are completed instead.

`return_exceptions` can be used to treat exceptions as successful results:

```
@app.function()
def my_func(a):
    if a == 2:
        raise Exception("ohno")
    return a ** 2

@app.local_entrypoint()
def main():
    # [0, 1, UserCodeException(Exception('ohno'))]
    print(list(my_func.map(range(3), return_exceptions=True)))
```

Copy

### starmap

```
@warn_if_generator_is_not_consumed(function_name="Function.starmap.aio")
def starmap(
    self,
    input_iterator: typing.Iterable[typing.Sequence[Any]],
    kwargs={},
    order_outputs: bool = True,
    return_exceptions: bool = False,
) -> AsyncOrSyncIterable:
```

Copy

Like `map`, but spreads arguments over multiple function arguments.

Assumes every input is a sequence (e.g. a tuple).

Example:

```
@app.function()
def my_func(a, b):
    return a + b

@app.local_entrypoint()
def main():
    assert list(my_func.starmap([(1, 2), (3, 4)])) == [3, 7]
```

Copy

### for\_each

```
def for_each(self, *input_iterators, kwargs={}, ignore_exceptions: bool = False):
```

Copy

Execute function for all inputs, ignoring outputs.

Convenient alias for `.map()` in cases where the function just needs to be called.
as the caller doesn’t have to consume the generator to process the inputs.

## modal.functions.FunctionCall

```
class FunctionCall(typing.Generic, modal.object.Object)
```

Copy

A reference to an executed function call.

Constructed using `.spawn(...)` on a Modal function with the same
arguments that a function normally takes. Acts as a reference to
an ongoing function call that can be passed around and used to
poll or fetch function results at some later time.

Conceptually similar to a Future/Promise/AsyncResult in other contexts and languages.

```
def __init__(self, *args, **kwargs):
```

Copy

### hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

### get

```
def get(self, timeout: Optional[float] = None) -> ReturnType:
```

Copy

Get the result of the function call.

This function waits indefinitely by default. It takes an optional
`timeout` argument that specifies the maximum number of seconds to wait,
which can be set to `0` to poll for an output immediately.

The returned coroutine is not cancellation-safe.

### get\_gen

```
def get_gen(self) -> AsyncGenerator[Any, None]:
```

Copy

Calls the generator remotely, executing it with the given arguments and returning the execution’s result.

### get\_call\_graph

```
def get_call_graph(self) -> list[InputInfo]:
```

Copy

Returns a structure representing the call graph from a given root
call ID, along with the status of execution for each node.

See [`modal.call_graph`](https://modal.com/docs/reference/modal.call_graph) reference page
for documentation on the structure of the returned `InputInfo` items.

### cancel

```
def cancel(
    self,
    terminate_containers: bool = False,  # if true, containers running the inputs are forcibly terminated
):
```

Copy

Cancels the function call, which will stop its execution and mark its inputs as
[`TERMINATED`](https://modal.com/docs/reference/modal.call_graph#modalcall_graphinputstatus).

If `terminate_containers=True` \- the containers running the cancelled inputs are all terminated
causing any non-cancelled inputs on those containers to be rescheduled in new containers.

### from\_id

```
@staticmethod
def from_id(
    function_call_id: str, client: Optional[_Client] = None, is_generator: bool = False
) -> "_FunctionCall":
```

Copy

## modal.functions.FunctionStats

```
class FunctionStats(object)
```

Copy

Simple data structure storing stats for a running function.

```
def __init__(self, backlog: int, num_total_runners: int) -> None
```

Copy

## modal.functions.gather

```
async def gather(*function_calls: _FunctionCall[ReturnType]) -> typing.Sequence[ReturnType]:
```

Copy

Wait until all Modal function calls have results before returning

Accepts a variable number of FunctionCall objects as returned by `Function.spawn()`.

Returns a list of results from each function call, or raises an exception
of the first failing function call.

E.g.

```
function_call_1 = slow_func_1.spawn()
function_call_2 = slow_func_2.spawn()

result_1, result_2 = gather(function_call_1, function_call_2)
```

Copy

[modal.functions](https://modal.com/docs/reference/modal.Function#modalfunctions) [modal.functions.Function](https://modal.com/docs/reference/modal.Function#modalfunctionsfunction) [hydrate](https://modal.com/docs/reference/modal.Function#hydrate) [keep\_warm](https://modal.com/docs/reference/modal.Function#keep_warm) [from\_name](https://modal.com/docs/reference/modal.Function#from_name) [lookup](https://modal.com/docs/reference/modal.Function#lookup) [web\_url](https://modal.com/docs/reference/modal.Function#web_url) [remote](https://modal.com/docs/reference/modal.Function#remote) [remote\_gen](https://modal.com/docs/reference/modal.Function#remote_gen) [local](https://modal.com/docs/reference/modal.Function#local) [spawn](https://modal.com/docs/reference/modal.Function#spawn) [get\_raw\_f](https://modal.com/docs/reference/modal.Function#get_raw_f) [get\_current\_stats](https://modal.com/docs/reference/modal.Function#get_current_stats) [map](https://modal.com/docs/reference/modal.Function#map) [starmap](https://modal.com/docs/reference/modal.Function#starmap) [for\_each](https://modal.com/docs/reference/modal.Function#for_each) [modal.functions.FunctionCall](https://modal.com/docs/reference/modal.Function#modalfunctionsfunctioncall) [hydrate](https://modal.com/docs/reference/modal.Function#hydrate-1) [get](https://modal.com/docs/reference/modal.Function#get) [get\_gen](https://modal.com/docs/reference/modal.Function#get_gen) [get\_call\_graph](https://modal.com/docs/reference/modal.Function#get_call_graph) [cancel](https://modal.com/docs/reference/modal.Function#cancel) [from\_id](https://modal.com/docs/reference/modal.Function#from_id) [modal.functions.FunctionStats](https://modal.com/docs/reference/modal.Function#modalfunctionsfunctionstats) [modal.functions.gather](https://modal.com/docs/reference/modal.Function#modalfunctionsgather)

* * *

# modal.Image

```
class Image(modal.object.Object)
```

Copy

Base class for container images to run functions in.

Do not construct this class directly; instead use one of its static factory methods,
such as `modal.Image.debian_slim`, `modal.Image.from_registry`, or `modal.Image.micromamba`.

```
def __init__(self, *args, **kwargs):
```

Copy

## hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

## copy\_mount

```
def copy_mount(self, mount: _Mount, remote_path: Union[str, Path] = ".") -> "_Image":
```

Copy

**Deprecated**: Use image.add\_local\_dir(…, copy=True) or similar instead.

Copy the entire contents of a `modal.Mount` into an image.
Useful when files only available locally are required during the image
build process.

**Example**

```
static_images_dir = "./static"
# place all static images in root of mount
mount = modal.Mount.from_local_dir(static_images_dir, remote_path="/")
# place mount's contents into /static directory of image.
image = modal.Image.debian_slim().copy_mount(mount, remote_path="/static")
```

Copy

## add\_local\_file

```
def add_local_file(self, local_path: Union[str, Path], remote_path: str, *, copy: bool = False) -> "_Image":
```

Copy

Adds a local file to the image at `remote_path` within the container

By default ( `copy=False`), the files are added to containers on startup and are not built into the actual Image,
which speeds up deployment.

Set `copy=True` to copy the files into an Image layer at build time instead, similar to how
[`COPY`](https://docs.docker.com/engine/reference/builder/#copy) works in a `Dockerfile`.

copy=True can slow down iteration since it requires a rebuild of the Image and any subsequent
build steps whenever the included files change, but it is required if you want to run additional
build steps after this one.

## add\_local\_dir

```
def add_local_dir(
    self,
    local_path: Union[str, Path],
    remote_path: str,
    *,
    copy: bool = False,
    # Predicate filter function for file exclusion, which should accept a filepath and return `True` for exclusion.
    # Defaults to excluding no files. If a Sequence is provided, it will be converted to a FilePatternMatcher.
    # Which follows dockerignore syntax.
    ignore: Union[Sequence[str], Callable[[Path], bool]] = [],
) -> "_Image":
```

Copy

Adds a local directory’s content to the image at `remote_path` within the container

By default ( `copy=False`), the files are added to containers on startup and are not built into the actual Image,
which speeds up deployment.

Set `copy=True` to copy the files into an Image layer at build time instead, similar to how
[`COPY`](https://docs.docker.com/engine/reference/builder/#copy) works in a `Dockerfile`.

copy=True can slow down iteration since it requires a rebuild of the Image and any subsequent
build steps whenever the included files change, but it is required if you want to run additional
build steps after this one.

**Usage:**

```
from modal import FilePatternMatcher

image = modal.Image.debian_slim().add_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=["*.venv"],
)

image = modal.Image.debian_slim().add_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=lambda p: p.is_relative_to(".venv"),
)

image = modal.Image.debian_slim().add_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=FilePatternMatcher("**/*.txt"),
)

# When including files is simpler than excluding them, you can use the `~` operator to invert the matcher.
image = modal.Image.debian_slim().add_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=~FilePatternMatcher("**/*.py"),
)

# You can also read ignore patterns from a file.
image = modal.Image.debian_slim().add_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=FilePatternMatcher.from_file("/path/to/ignorefile"),
)
```

Copy

## copy\_local\_file

```
def copy_local_file(self, local_path: Union[str, Path], remote_path: Union[str, Path] = "./") -> "_Image":
```

Copy

Copy a file into the image as a part of building it.

This works in a similar way to [`COPY`](https://docs.docker.com/engine/reference/builder/#copy)
works in a `Dockerfile`.

## add\_local\_python\_source

```
def add_local_python_source(
    self, *modules: str, copy: bool = False, ignore: Union[Sequence[str], Callable[[Path], bool]] = NON_PYTHON_FILES
) -> "_Image":
```

Copy

Adds locally available Python packages/modules to containers

Adds all files from the specified Python package or module to containers running the Image.

Packages are added to the `/root` directory of containers, which is on the `PYTHONPATH`
of any executed Modal Functions, enabling import of the module by that name.

By default ( `copy=False`), the files are added to containers on startup and are not built into the actual Image,
which speeds up deployment.

Set `copy=True` to copy the files into an Image layer at build time instead. This can slow down iteration since
it requires a rebuild of the Image and any subsequent build steps whenever the included files change, but it is
required if you want to run additional build steps after this one.

**Note:** This excludes all dot-prefixed subdirectories or files and all `.pyc`/ `__pycache__` files.
To add full directories with finer control, use `.add_local_dir()` instead and specify `/root` as
the destination directory.

By default only includes `.py`-files in the source modules. Set the `ignore` argument to a list of patterns
or a callable to override this behavior, e.g.:

```
# includes everything except data.json
modal.Image.debian_slim().add_local_python_source("mymodule", ignore=["data.json"])

# exclude large files
modal.Image.debian_slim().add_local_python_source(
    "mymodule",
    ignore=lambda p: p.stat().st_size > 1e9
)
```

Copy

## copy\_local\_dir

```
def copy_local_dir(
    self,
    local_path: Union[str, Path],
    remote_path: Union[str, Path] = ".",
    # Predicate filter function for file exclusion, which should accept a filepath and return `True` for exclusion.
    # Defaults to excluding no files. If a Sequence is provided, it will be converted to a FilePatternMatcher.
    # Which follows dockerignore syntax.
    ignore: Union[Sequence[str], Callable[[Path], bool]] = [],
) -> "_Image":
```

Copy

**Deprecated**: Use image.add\_local\_dir instead

Copy a directory into the image as a part of building the image.

This works in a similar way to [`COPY`](https://docs.docker.com/engine/reference/builder/#copy)
works in a `Dockerfile`.

**Usage:**

```
from pathlib import Path
from modal import FilePatternMatcher

image = modal.Image.debian_slim().copy_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=["**/*.venv"],
)

image = modal.Image.debian_slim().copy_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=lambda p: p.is_relative_to(".venv"),
)

image = modal.Image.debian_slim().copy_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=FilePatternMatcher("**/*.txt"),
)

# When including files is simpler than excluding them, you can use the `~` operator to invert the matcher.
image = modal.Image.debian_slim().copy_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=~FilePatternMatcher("**/*.py"),
)

# You can also read ignore patterns from a file.
image = modal.Image.debian_slim().copy_local_dir(
    "~/assets",
    remote_path="/assets",
    ignore=FilePatternMatcher.from_file("/path/to/ignorefile"),
)
```

Copy

## from\_id

```
@staticmethod
def from_id(image_id: str, client: Optional[_Client] = None) -> "_Image":
```

Copy

Construct an Image from an id and look up the Image result.

The ID of an Image object can be accessed using `.object_id`.

## pip\_install

```
def pip_install(
    self,
    *packages: Union[str, list[str]],  # A list of Python packages, eg. ["numpy", "matplotlib>=3.5.0"]
    find_links: Optional[str] = None,  # Passes -f (--find-links) pip install
    index_url: Optional[str] = None,  # Passes -i (--index-url) to pip install
    extra_index_url: Optional[str] = None,  # Passes --extra-index-url to pip install
    pre: bool = False,  # Passes --pre (allow pre-releases) to pip install
    extra_options: str = "",  # Additional options to pass to pip install, e.g. "--no-build-isolation --no-clean"
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
) -> "_Image":
```

Copy

Install a list of Python packages using pip.

**Examples**

Simple installation:

```
image = modal.Image.debian_slim().pip_install("click", "httpx~=0.23.3")
```

Copy

More complex installation:

```
image = (
    modal.Image.from_registry(
        "nvidia/cuda:12.2.0-devel-ubuntu22.04", add_python="3.11"
    )
    .pip_install(
        "ninja",
        "packaging",
        "wheel",
        "transformers==4.40.2",
    )
    .pip_install(
        "flash-attn==2.5.8", extra_options="--no-build-isolation"
    )
)
```

Copy

## pip\_install\_private\_repos

```
def pip_install_private_repos(
    self,
    *repositories: str,
    git_user: str,
    find_links: Optional[str] = None,  # Passes -f (--find-links) pip install
    index_url: Optional[str] = None,  # Passes -i (--index-url) to pip install
    extra_index_url: Optional[str] = None,  # Passes --extra-index-url to pip install
    pre: bool = False,  # Passes --pre (allow pre-releases) to pip install
    extra_options: str = "",  # Additional options to pass to pip install, e.g. "--no-build-isolation --no-clean"
    gpu: GPU_T = None,
    secrets: Sequence[_Secret] = [],
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
) -> "_Image":
```

Copy

Install a list of Python packages from private git repositories using pip.

This method currently supports Github and Gitlab only.

- **Github:** Provide a `modal.Secret` that contains a `GITHUB_TOKEN` key-value pair
- **Gitlab:** Provide a `modal.Secret` that contains a `GITLAB_TOKEN` key-value pair

These API tokens should have permissions to read the list of private repositories provided as arguments.

We recommend using Github’s [‘fine-grained’ access tokens](https://github.blog/2022-10-18-introducing-fine-grained-personal-access-tokens-for-github/).
These tokens are repo-scoped, and avoid granting read permission across all of a user’s private repos.

**Example**

```
image = (
    modal.Image
    .debian_slim()
    .pip_install_private_repos(
        "github.com/ecorp/private-one@1.0.0",
        "github.com/ecorp/private-two@main"
        "github.com/ecorp/private-three@d4776502"
        # install from 'inner' directory on default branch.
        "github.com/ecorp/private-four#subdirectory=inner",
        git_user="erikbern",
        secrets=[modal.Secret.from_name("github-read-private")],
    )
)
```

Copy

## pip\_install\_from\_requirements

```
def pip_install_from_requirements(
    self,
    requirements_txt: str,  # Path to a requirements.txt file.
    find_links: Optional[str] = None,  # Passes -f (--find-links) pip install
    *,
    index_url: Optional[str] = None,  # Passes -i (--index-url) to pip install
    extra_index_url: Optional[str] = None,  # Passes --extra-index-url to pip install
    pre: bool = False,  # Passes --pre (allow pre-releases) to pip install
    extra_options: str = "",  # Additional options to pass to pip install, e.g. "--no-build-isolation --no-clean"
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
) -> "_Image":
```

Copy

Install a list of Python packages from a local `requirements.txt` file.

## pip\_install\_from\_pyproject

```
def pip_install_from_pyproject(
    self,
    pyproject_toml: str,
    optional_dependencies: list[str] = [],
    *,
    find_links: Optional[str] = None,  # Passes -f (--find-links) pip install
    index_url: Optional[str] = None,  # Passes -i (--index-url) to pip install
    extra_index_url: Optional[str] = None,  # Passes --extra-index-url to pip install
    pre: bool = False,  # Passes --pre (allow pre-releases) to pip install
    extra_options: str = "",  # Additional options to pass to pip install, e.g. "--no-build-isolation --no-clean"
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
) -> "_Image":
```

Copy

Install dependencies specified by a local `pyproject.toml` file.

`optional_dependencies` is a list of the keys of the
optional-dependencies section(s) of the `pyproject.toml` file
(e.g. test, doc, experiment, etc). When provided,
all of the packages in each listed section are installed as well.

## poetry\_install\_from\_file

```
def poetry_install_from_file(
    self,
    poetry_pyproject_toml: str,
    # Path to the lockfile. If not provided, uses poetry.lock in the same directory.
    poetry_lockfile: Optional[str] = None,
    # If set to True, it will not use poetry.lock
    ignore_lockfile: bool = False,
    # If set to True, use old installer. See https://github.com/python-poetry/poetry/issues/3336
    old_installer: bool = False,
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    # Selected optional dependency groups to install (See https://python-poetry.org/docs/cli/#install)
    with_: list[str] = [],
    # Selected optional dependency groups to exclude (See https://python-poetry.org/docs/cli/#install)
    without: list[str] = [],
    # Only install dependency groups specifed in this list.
    only: list[str] = [],
    *,
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
) -> "_Image":
```

Copy

Install poetry _dependencies_ specified by a local `pyproject.toml` file.

If not provided as argument the path to the lockfile is inferred. However, the
file has to exist, unless `ignore_lockfile` is set to `True`.

Note that the root project of the poetry project is not installed, only the dependencies.
For including local python source files see `add_local_python_source`

## dockerfile\_commands

```
def dockerfile_commands(
    self,
    *dockerfile_commands: Union[str, list[str]],
    context_files: dict[str, str] = {},
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
    # modal.Mount with local files to supply as build context for COPY commands
    context_mount: Optional[_Mount] = None,
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    ignore: Union[Sequence[str], Callable[[Path], bool]] = AUTO_DOCKERIGNORE,
) -> "_Image":
```

Copy

Extend an image with arbitrary Dockerfile-like commands.

**Usage:**

```
from modal import FilePatternMatcher

# By default a .dockerignore file is used if present in the current working directory
image = modal.Image.debian_slim().dockerfile_commands(
    ["COPY data /data"],
)

image = modal.Image.debian_slim().dockerfile_commands(
    ["COPY data /data"],
    ignore=["*.venv"],
)

image = modal.Image.debian_slim().dockerfile_commands(
    ["COPY data /data"],
    ignore=lambda p: p.is_relative_to(".venv"),
)

image = modal.Image.debian_slim().dockerfile_commands(
    ["COPY data /data"],
    ignore=FilePatternMatcher("**/*.txt"),
)

# When including files is simpler than excluding them, you can use the `~` operator to invert the matcher.
image = modal.Image.debian_slim().dockerfile_commands(
    ["COPY data /data"],
    ignore=~FilePatternMatcher("**/*.py"),
)

# You can also read ignore patterns from a file.
image = modal.Image.debian_slim().dockerfile_commands(
    ["COPY data /data"],
    ignore=FilePatternMatcher.from_file("/path/to/dockerignore"),
)
```

Copy

## entrypoint

```
def entrypoint(
    self,
    entrypoint_commands: list[str],
) -> "_Image":
```

Copy

Set the entrypoint for the image.

## shell

```
def shell(
    self,
    shell_commands: list[str],
) -> "_Image":
```

Copy

Overwrite default shell for the image.

## run\_commands

```
def run_commands(
    self,
    *commands: Union[str, list[str]],
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
) -> "_Image":
```

Copy

Extend an image with a list of shell commands to run.

## micromamba

```
@staticmethod
def micromamba(
    python_version: Optional[str] = None,
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
) -> "_Image":
```

Copy

A Micromamba base image. Micromamba allows for fast building of small Conda-based containers.

## micromamba\_install

```
def micromamba_install(
    self,
    # A list of Python packages, eg. ["numpy", "matplotlib>=3.5.0"]
    *packages: Union[str, list[str]],
    # A local path to a file containing package specifications
    spec_file: Optional[str] = None,
    # A list of Conda channels, eg. ["conda-forge", "nvidia"].
    channels: list[str] = [],
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
) -> "_Image":
```

Copy

Install a list of additional packages using micromamba.

## from\_registry

```
@staticmethod
def from_registry(
    tag: str,
    *,
    secret: Optional[_Secret] = None,
    setup_dockerfile_commands: list[str] = [],
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    add_python: Optional[str] = None,
    **kwargs,
) -> "_Image":
```

Copy

Build a Modal image from a public or private image registry, such as Docker Hub.

The image must be built for the `linux/amd64` platform.

If your image does not come with Python installed, you can use the `add_python` parameter
to specify a version of Python to add to the image. Otherwise, the image is expected to
have Python on PATH as `python`, along with `pip`.

You may also use `setup_dockerfile_commands` to run Dockerfile commands before the
remaining commands run. This might be useful if you want a custom Python installation or to
set a `SHELL`. Prefer `run_commands()` when possible though.

To authenticate against a private registry with static credentials, you must set the `secret` parameter to
a `modal.Secret` containing a username ( `REGISTRY_USERNAME`) and
an access token or password ( `REGISTRY_PASSWORD`).

To authenticate against private registries with credentials from a cloud provider,
use `Image.from_gcp_artifact_registry()` or `Image.from_aws_ecr()`.

**Examples**

```
modal.Image.from_registry("python:3.11-slim-bookworm")
modal.Image.from_registry("ubuntu:22.04", add_python="3.11")
modal.Image.from_registry("nvcr.io/nvidia/pytorch:22.12-py3")
```

Copy

## from\_gcp\_artifact\_registry

```
@staticmethod
def from_gcp_artifact_registry(
    tag: str,
    secret: Optional[_Secret] = None,
    *,
    setup_dockerfile_commands: list[str] = [],
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    add_python: Optional[str] = None,
    **kwargs,
) -> "_Image":
```

Copy

Build a Modal image from a private image in Google Cloud Platform (GCP) Artifact Registry.

You will need to pass a `modal.Secret` containing [your GCP service account key data](https://cloud.google.com/iam/docs/keys-create-delete#creating)
as `SERVICE_ACCOUNT_JSON`. This can be done from the [Secrets](https://modal.com/secrets) page.
Your service account should be granted a specific role depending on the GCP registry used:

- For Artifact Registry images ( `pkg.dev` domains) use
the [“Artifact Registry Reader”](https://cloud.google.com/artifact-registry/docs/access-control#roles) role
- For Container Registry images ( `gcr.io` domains) use
the [“Storage Object Viewer”](https://cloud.google.com/artifact-registry/docs/transition/setup-gcr-repo) role

**Note:** This method does not use `GOOGLE_APPLICATION_CREDENTIALS` as that
variable accepts a path to a JSON file, not the actual JSON string.

See `Image.from_registry()` for information about the other parameters.

**Example**

```
modal.Image.from_gcp_artifact_registry(
    "us-east1-docker.pkg.dev/my-project-1234/my-repo/my-image:my-version",
    secret=modal.Secret.from_name(
        "my-gcp-secret",
        required_keys=["SERVICE_ACCOUNT_JSON"],
    ),
    add_python="3.11",
)
```

Copy

## from\_aws\_ecr

```
@staticmethod
def from_aws_ecr(
    tag: str,
    secret: Optional[_Secret] = None,
    *,
    setup_dockerfile_commands: list[str] = [],
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    add_python: Optional[str] = None,
    **kwargs,
) -> "_Image":
```

Copy

Build a Modal image from a private image in AWS Elastic Container Registry (ECR).

You will need to pass a `modal.Secret` containing `AWS_ACCESS_KEY_ID`,
`AWS_SECRET_ACCESS_KEY`, and `AWS_REGION` to access the target ECR registry.

IAM configuration details can be found in the AWS documentation for
[“Private repository policies”](https://docs.aws.amazon.com/AmazonECR/latest/userguide/repository-policies.html).

See `Image.from_registry()` for information about the other parameters.

**Example**

```
modal.Image.from_aws_ecr(
    "000000000000.dkr.ecr.us-east-1.amazonaws.com/my-private-registry:my-version",
    secret=modal.Secret.from_name(
        "aws",
        required_keys=["AWS_ACCESS_KEY_ID", "AWS_SECRET_ACCESS_KEY", "AWS_REGION"],
    ),
    add_python="3.11",
)
```

Copy

## from\_dockerfile

```
@staticmethod
def from_dockerfile(
    # Filepath to Dockerfile.
    path: Union[str, Path],
    # modal.Mount with local files to supply as build context for COPY commands.
    # NOTE: The remote_path of the Mount should match the Dockerfile's WORKDIR.
    context_mount: Optional[_Mount] = None,
    # Ignore cached builds, similar to 'docker build --no-cache'
    force_build: bool = False,
    *,
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
    add_python: Optional[str] = None,
    ignore: Union[Sequence[str], Callable[[Path], bool]] = AUTO_DOCKERIGNORE,
) -> "_Image":
```

Copy

Build a Modal image from a local Dockerfile.

If your Dockerfile does not have Python installed, you can use the `add_python` parameter
to specify a version of Python to add to the image.

**Usage:**

```
from modal import FilePatternMatcher

# By default a .dockerignore file is used if present in the current working directory
image = modal.Image.from_dockerfile(
    "./Dockerfile",
    add_python="3.12",
)

image = modal.Image.from_dockerfile(
    "./Dockerfile",
    add_python="3.12",
    ignore=["*.venv"],
)

image = modal.Image.from_dockerfile(
    "./Dockerfile",
    add_python="3.12",
    ignore=lambda p: p.is_relative_to(".venv"),
)

image = modal.Image.from_dockerfile(
    "./Dockerfile",
    add_python="3.12",
    ignore=FilePatternMatcher("**/*.txt"),
)

# When including files is simpler than excluding them, you can use the `~` operator to invert the matcher.
image = modal.Image.from_dockerfile(
    "./Dockerfile",
    add_python="3.12",
    ignore=~FilePatternMatcher("**/*.py"),
)

# You can also read ignore patterns from a file.
image = modal.Image.from_dockerfile(
    "./Dockerfile",
    add_python="3.12",
    ignore=FilePatternMatcher.from_file("/path/to/dockerignore"),
)
```

Copy

## debian\_slim

```
@staticmethod
def debian_slim(python_version: Optional[str] = None, force_build: bool = False) -> "_Image":
```

Copy

Default image, based on the official `python` Docker images.

## apt\_install

```
def apt_install(
    self,
    *packages: Union[str, list[str]],  # A list of packages, e.g. ["ssh", "libpq-dev"]
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    secrets: Sequence[_Secret] = [],
    gpu: GPU_T = None,
) -> "_Image":
```

Copy

Install a list of Debian packages using `apt`.

**Example**

```
image = modal.Image.debian_slim().apt_install("git")
```

Copy

## run\_function

```
def run_function(
    self,
    raw_f: Callable[..., Any],
    secrets: Sequence[_Secret] = (),  # Optional Modal Secret objects with environment variables for the container
    gpu: Union[\
        GPU_T, list[GPU_T]\
    ] = None,  # GPU request as string ("any", "T4", ...), object (`modal.GPU.A100()`, ...), or a list of either
    mounts: Sequence[_Mount] = (),  # Mounts attached to the function
    volumes: dict[Union[str, PurePosixPath], Union[_Volume, _CloudBucketMount]] = {},  # Volume mount paths
    network_file_systems: dict[Union[str, PurePosixPath], _NetworkFileSystem] = {},  # NFS mount paths
    cpu: Optional[float] = None,  # How many CPU cores to request. This is a soft limit.
    memory: Optional[int] = None,  # How much memory to request, in MiB. This is a soft limit.
    timeout: Optional[int] = 60 * 60,  # Maximum execution time of the function in seconds.
    force_build: bool = False,  # Ignore cached builds, similar to 'docker build --no-cache'
    cloud: Optional[str] = None,  # Cloud provider to run the function on. Possible values are aws, gcp, oci, auto.
    region: Optional[Union[str, Sequence[str]]] = None,  # Region or regions to run the function on.
    args: Sequence[Any] = (),  # Positional arguments to the function.
    kwargs: dict[str, Any] = {},  # Keyword arguments to the function.
) -> "_Image":
```

Copy

Run user-defined function `raw_f` as an image build step. The function runs just like an ordinary Modal
function, and any kwargs accepted by `@app.function` (such as `Mount` s, `NetworkFileSystem` s,
and resource requests) can be supplied to it.
After it finishes execution, a snapshot of the resulting container file system is saved as an image.

**Note**

Only the source code of `raw_f`, the contents of `**kwargs`, and any referenced _global_ variables
are used to determine whether the image has changed and needs to be rebuilt.
If this function references other functions or variables, the image will not be rebuilt if you
make changes to them. You can force a rebuild by changing the function’s source code itself.

**Example**

```

def my_build_function():
    open("model.pt", "w").write("parameters!")

image = (
    modal.Image
        .debian_slim()
        .pip_install("torch")
        .run_function(my_build_function, secrets=[...], mounts=[...])
)
```

Copy

## env

```
def env(self, vars: dict[str, str]) -> "_Image":
```

Copy

Sets the environment variables in an Image.

**Example**

```
image = (
    modal.Image.debian_slim()
    .env({"HF_HUB_ENABLE_HF_TRANSFER": "1"})
)
```

Copy

## workdir

```
def workdir(self, path: Union[str, PurePosixPath]) -> "_Image":
```

Copy

Set the working directory for subsequent image build steps and function execution.

**Example**

```
image = (
    modal.Image.debian_slim()
    .run_commands("git clone https://xyz app")
    .workdir("/app")
    .run_commands("yarn install")
)
```

Copy

## imports

```
@contextlib.contextmanager
def imports(self):
```

Copy

Used to import packages in global scope that are only available when running remotely.
By using this context manager you can avoid an `ImportError` due to not having certain
packages installed locally.

**Usage:**

```
with image.imports():
    import torch
```

Copy

[modal.Image](https://modal.com/docs/reference/modal.Image#modalimage) [hydrate](https://modal.com/docs/reference/modal.Image#hydrate) [copy\_mount](https://modal.com/docs/reference/modal.Image#copy_mount) [add\_local\_file](https://modal.com/docs/reference/modal.Image#add_local_file) [add\_local\_dir](https://modal.com/docs/reference/modal.Image#add_local_dir) [copy\_local\_file](https://modal.com/docs/reference/modal.Image#copy_local_file) [add\_local\_python\_source](https://modal.com/docs/reference/modal.Image#add_local_python_source) [copy\_local\_dir](https://modal.com/docs/reference/modal.Image#copy_local_dir) [from\_id](https://modal.com/docs/reference/modal.Image#from_id) [pip\_install](https://modal.com/docs/reference/modal.Image#pip_install) [pip\_install\_private\_repos](https://modal.com/docs/reference/modal.Image#pip_install_private_repos) [pip\_install\_from\_requirements](https://modal.com/docs/reference/modal.Image#pip_install_from_requirements) [pip\_install\_from\_pyproject](https://modal.com/docs/reference/modal.Image#pip_install_from_pyproject) [poetry\_install\_from\_file](https://modal.com/docs/reference/modal.Image#poetry_install_from_file) [dockerfile\_commands](https://modal.com/docs/reference/modal.Image#dockerfile_commands) [entrypoint](https://modal.com/docs/reference/modal.Image#entrypoint) [shell](https://modal.com/docs/reference/modal.Image#shell) [run\_commands](https://modal.com/docs/reference/modal.Image#run_commands) [micromamba](https://modal.com/docs/reference/modal.Image#micromamba) [micromamba\_install](https://modal.com/docs/reference/modal.Image#micromamba_install) [from\_registry](https://modal.com/docs/reference/modal.Image#from_registry) [from\_gcp\_artifact\_registry](https://modal.com/docs/reference/modal.Image#from_gcp_artifact_registry) [from\_aws\_ecr](https://modal.com/docs/reference/modal.Image#from_aws_ecr) [from\_dockerfile](https://modal.com/docs/reference/modal.Image#from_dockerfile) [debian\_slim](https://modal.com/docs/reference/modal.Image#debian_slim) [apt\_install](https://modal.com/docs/reference/modal.Image#apt_install) [run\_function](https://modal.com/docs/reference/modal.Image#run_function) [env](https://modal.com/docs/reference/modal.Image#env) [workdir](https://modal.com/docs/reference/modal.Image#workdir) [imports](https://modal.com/docs/reference/modal.Image#imports)

* * *

# modal.Mount

```
class Mount(modal.object.Object)
```

Copy

**Deprecated**: Mounts should not be used explicitly anymore, use `Image.add_local_*` commands instead.

Create a mount for a local directory or file that can be attached
to one or more Modal functions.

**Usage**

```
import modal
import os
app = modal.App()

@app.function(mounts=[modal.Mount.from_local_dir("~/foo", remote_path="/root/foo")])
def f():
    # `/root/foo` has the contents of `~/foo`.
    print(os.listdir("/root/foo/"))
```

Copy

Modal syncs the contents of the local directory every time the app runs, but uses the hash of
the file’s contents to skip uploading files that have been uploaded before.

```
def __init__(self, *args, **kwargs):
```

Copy

## hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

## add\_local\_dir

```
def add_local_dir(
    self,
    local_path: Union[str, Path],
    *,
    # Where the directory is placed within in the mount
    remote_path: Union[str, PurePosixPath, None] = None,
    # Predicate filter function for file selection, which should accept a filepath and return `True` for inclusion.
    # Defaults to including all files.
    condition: Optional[Callable[[str], bool]] = None,
    # add files from subdirectories as well
    recursive: bool = True,
) -> "_Mount":
```

Copy

Add a local directory to the `Mount` object.

## from\_local\_dir

```
@staticmethod
def from_local_dir(
    local_path: Union[str, Path],
    *,
    # Where the directory is placed within in the mount
    remote_path: Union[str, PurePosixPath, None] = None,
    # Predicate filter function for file selection, which should accept a filepath and return `True` for inclusion.
    # Defaults to including all files.
    condition: Optional[Callable[[str], bool]] = None,
    # add files from subdirectories as well
    recursive: bool = True,
) -> "_Mount":
```

Copy

**Deprecated:** Use image.add\_local\_dir() instead

Create a `Mount` from a local directory.

**Usage**

```
assets = modal.Mount.from_local_dir(
    "~/assets",
    condition=lambda pth: not ".venv" in pth,
    remote_path="/assets",
)
```

Copy

## add\_local\_file

```
def add_local_file(
    self,
    local_path: Union[str, Path],
    remote_path: Union[str, PurePosixPath, None] = None,
) -> "_Mount":
```

Copy

Add a local file to the `Mount` object.

## from\_local\_file

```
@staticmethod
def from_local_file(local_path: Union[str, Path], remote_path: Union[str, PurePosixPath, None] = None) -> "_Mount":
```

Copy

**Deprecated**: Use image.add\_local\_file() instead

Create a `Mount` mounting a single local file.

**Usage**

```
# Mount the DBT profile in user's home directory into container.
dbt_profiles = modal.Mount.from_local_file(
    local_path="~/profiles.yml",
    remote_path="/root/dbt_profile/profiles.yml",
)
```

Copy

## from\_local\_python\_packages

```
@staticmethod
def from_local_python_packages(
    *module_names: str,
    remote_dir: Union[str, PurePosixPath] = ROOT_DIR.as_posix(),
    # Predicate filter function for file selection, which should accept a filepath and return `True` for inclusion.
    # Defaults to including all files.
    condition: Optional[Callable[[str], bool]] = None,
    ignore: Optional[Union[Sequence[str], Callable[[Path], bool]]] = None,
) -> "_Mount":
```

Copy

**Deprecated**: Use image.add\_local\_python\_source instead

Returns a `modal.Mount` that makes local modules listed in `module_names` available inside the container.
This works by mounting the local path of each module’s package to a directory inside the container
that’s on `PYTHONPATH`.

**Usage**

```
import modal
import my_local_module

app = modal.App()

@app.function(mounts=[\
    modal.Mount.from_local_python_packages("my_local_module", "my_other_module"),\
])
def f():
    my_local_module.do_stuff()
```

Copy

[modal.Mount](https://modal.com/docs/reference/modal.Mount#modalmount) [hydrate](https://modal.com/docs/reference/modal.Mount#hydrate) [add\_local\_dir](https://modal.com/docs/reference/modal.Mount#add_local_dir) [from\_local\_dir](https://modal.com/docs/reference/modal.Mount#from_local_dir) [add\_local\_file](https://modal.com/docs/reference/modal.Mount#add_local_file) [from\_local\_file](https://modal.com/docs/reference/modal.Mount#from_local_file) [from\_local\_python\_packages](https://modal.com/docs/reference/modal.Mount#from_local_python_packages)

* * *

# modal.NetworkFileSystem

```
class NetworkFileSystem(modal.object.Object)
```

Copy

A shared, writable file system accessible by one or more Modal functions.

By attaching this file system as a mount to one or more functions, they can
share and persist data with each other.

**Usage**

```
import modal

nfs = modal.NetworkFileSystem.from_name("my-nfs", create_if_missing=True)
app = modal.App()

@app.function(network_file_systems={"/root/foo": nfs})
def f():
    pass

@app.function(network_file_systems={"/root/goo": nfs})
def g():
    pass
```

Copy

Also see the CLI methods for accessing network file systems:

```
modal nfs --help
```

Copy

A `NetworkFileSystem` can also be useful for some local scripting scenarios, e.g.:

```
nfs = modal.NetworkFileSystem.lookup("my-network-file-system")
for chunk in nfs.read_file("my_db_dump.csv"):
    ...
```

Copy

```
def __init__(self, *args, **kwargs):
```

Copy

## hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

## from\_name

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def from_name(
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
) -> "_NetworkFileSystem":
```

Copy

Reference a NetworkFileSystem by its name, creating if necessary.

In contrast to `modal.NetworkFileSystem.lookup`, this is a lazy method
that defers hydrating the local object with metadata from Modal servers
until the first time it is actually used.

```
nfs = NetworkFileSystem.from_name("my-nfs", create_if_missing=True)

@app.function(network_file_systems={"/data": nfs})
def f():
    pass
```

Copy

## ephemeral

```
@classmethod
@contextmanager
def ephemeral(
    cls: type["_NetworkFileSystem"],
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    _heartbeat_sleep: float = EPHEMERAL_OBJECT_HEARTBEAT_SLEEP,
) -> Iterator["_NetworkFileSystem"]:
```

Copy

Creates a new ephemeral network filesystem within a context manager:

Usage:

```
with modal.NetworkFileSystem.ephemeral() as nfs:
    assert nfs.listdir("/") == []
```

Copy

```
async with modal.NetworkFileSystem.ephemeral() as nfs:
    assert await nfs.listdir("/") == []
```

Copy

## lookup

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def lookup(
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
) -> "_NetworkFileSystem":
```

Copy

Lookup a named NetworkFileSystem.

In contrast to `modal.NetworkFileSystem.from_name`, this is an eager method
that will hydrate the local object with metadata from Modal servers.

```
nfs = modal.NetworkFileSystem.lookup("my-nfs")
print(nfs.listdir("/"))
```

Copy

## delete

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def delete(name: str, client: Optional[_Client] = None, environment_name: Optional[str] = None):
```

Copy

## write\_file

```
@live_method
def write_file(self, remote_path: str, fp: BinaryIO, progress_cb: Optional[Callable[..., Any]] = None) -> int:
```

Copy

Write from a file object to a path on the network file system, atomically.

Will create any needed parent directories automatically.

If remote\_path ends with `/` it’s assumed to be a directory and the
file will be uploaded with its current name to that directory.

## read\_file

```
@live_method_gen
def read_file(self, path: str) -> Iterator[bytes]:
```

Copy

Read a file from the network file system

## iterdir

```
@live_method_gen
def iterdir(self, path: str) -> Iterator[FileEntry]:
```

Copy

Iterate over all files in a directory in the network file system.

- Passing a directory path lists all files in the directory (names are relative to the directory)
- Passing a file path returns a list containing only that file’s listing description
- Passing a glob path (including at least one \* or \*\* sequence) returns all files matching
that glob path (using absolute paths)

## add\_local\_file

```
@live_method
def add_local_file(
    self,
    local_path: Union[Path, str],
    remote_path: Optional[Union[str, PurePosixPath, None]] = None,
    progress_cb: Optional[Callable[..., Any]] = None,
):
```

Copy

## add\_local\_dir

```
@live_method
def add_local_dir(
    self,
    local_path: Union[Path, str],
    remote_path: Optional[Union[str, PurePosixPath, None]] = None,
    progress_cb: Optional[Callable[..., Any]] = None,
):
```

Copy

## listdir

```
@live_method
def listdir(self, path: str) -> list[FileEntry]:
```

Copy

List all files in a directory in the network file system.

- Passing a directory path lists all files in the directory (names are relative to the directory)
- Passing a file path returns a list containing only that file’s listing description
- Passing a glob path (including at least one \* or \*\* sequence) returns all files matching
that glob path (using absolute paths)

## remove\_file

```
@live_method
def remove_file(self, path: str, recursive=False):
```

Copy

Remove a file in a network file system.

[modal.NetworkFileSystem](https://modal.com/docs/reference/modal.NetworkFileSystem#modalnetworkfilesystem) [hydrate](https://modal.com/docs/reference/modal.NetworkFileSystem#hydrate) [from\_name](https://modal.com/docs/reference/modal.NetworkFileSystem#from_name) [ephemeral](https://modal.com/docs/reference/modal.NetworkFileSystem#ephemeral) [lookup](https://modal.com/docs/reference/modal.NetworkFileSystem#lookup) [delete](https://modal.com/docs/reference/modal.NetworkFileSystem#delete) [write\_file](https://modal.com/docs/reference/modal.NetworkFileSystem#write_file) [read\_file](https://modal.com/docs/reference/modal.NetworkFileSystem#read_file) [iterdir](https://modal.com/docs/reference/modal.NetworkFileSystem#iterdir) [add\_local\_file](https://modal.com/docs/reference/modal.NetworkFileSystem#add_local_file) [add\_local\_dir](https://modal.com/docs/reference/modal.NetworkFileSystem#add_local_dir) [listdir](https://modal.com/docs/reference/modal.NetworkFileSystem#listdir) [remove\_file](https://modal.com/docs/reference/modal.NetworkFileSystem#remove_file)

* * *

# modal.Period

```
class Period(modal.schedule.Schedule)
```

Copy

Create a schedule that runs every given time interval.

**Usage**

```
import modal
app = modal.App()

@app.function(schedule=modal.Period(days=1))
def f():
    print("This function will run every day")

modal.Period(hours=4)          # runs every 4 hours
modal.Period(minutes=15)       # runs every 15 minutes
modal.Period(seconds=math.pi)  # runs every 3.141592653589793 seconds
```

Copy

Only `seconds` can be a float. All other arguments are integers.

Note that `days=1` will trigger the function the same time every day.
This does not have the same behavior as `seconds=84000` since days have
different lengths due to daylight savings and leap seconds. Similarly,
using `months=1` will trigger the function on the same day each month.

This behaves similar to the
[dateutil](https://dateutil.readthedocs.io/en/latest/relativedelta.html)
package.

```
def __init__(
    self,
    years: int = 0,
    months: int = 0,
    weeks: int = 0,
    days: int = 0,
    hours: int = 0,
    minutes: int = 0,
    seconds: float = 0,
) -> None:
```

Copy

[modal.Period](https://modal.com/docs/reference/modal.Period#modalperiod)

* * *

# modal.Proxy

```
class Proxy(modal.object.Object)
```

Copy

Proxy objects give your Modal containers a static outbound IP address.

This can be used for connecting to a remote address with network whitelist, for example
a database. See [the guide](https://modal.com/docs/guide/proxy-ips) for more information.

```
def __init__(self, *args, **kwargs):
```

Copy

## hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

## from\_name

```
@staticmethod
def from_name(
    name: str,
    environment_name: Optional[str] = None,
) -> "_Proxy":
```

Copy

Reference a Proxy by its name.

In contrast to most other Modal objects, new Proxy objects must be
provisioned via the Dashboard and cannot be created on the fly from code.

[modal.Proxy](https://modal.com/docs/reference/modal.Proxy#modalproxy) [hydrate](https://modal.com/docs/reference/modal.Proxy#hydrate) [from\_name](https://modal.com/docs/reference/modal.Proxy#from_name)

* * *

# modal.queue

## modal.queue.Queue

```
class Queue(modal.object.Object)
```

Copy

Distributed, FIFO queue for data flow in Modal apps.

The queue can contain any object serializable by `cloudpickle`, including Modal objects.

By default, the `Queue` object acts as a single FIFO queue which supports puts and gets (blocking and non-blocking).

**Usage**

```
from modal import Queue

# Create an ephemeral queue which is anonymous and garbage collected
with Queue.ephemeral() as my_queue:
    # Putting values
    my_queue.put("some value")
    my_queue.put(123)

    # Getting values
    assert my_queue.get() == "some value"
    assert my_queue.get() == 123

    # Using partitions
    my_queue.put(0)
    my_queue.put(1, partition="foo")
    my_queue.put(2, partition="bar")

    # Default and "foo" partition are ignored by the get operation.
    assert my_queue.get(partition="bar") == 2

    # Set custom 10s expiration time on "foo" partition.
    my_queue.put(3, partition="foo", partition_ttl=10)

    # (beta feature) Iterate through items in place (read immutably)
    my_queue.put(1)
    assert [v for v in my_queue.iterate()] == [0, 1]

# You can also create persistent queues that can be used across apps
queue = Queue.from_name("my-persisted-queue", create_if_missing=True)
queue.put(42)
assert queue.get() == 42
```

Copy

For more examples, see the [guide](https://modal.com/docs/guide/dicts-and-queues#modal-queues).

**Queue partitions (beta)**

Specifying partition keys gives access to other independent FIFO partitions within the same `Queue` object.
Across any two partitions, puts and gets are completely independent.
For example, a put in one partition does not affect a get in any other partition.

When no partition key is specified (by default), puts and gets will operate on a default partition.
This default partition is also isolated from all other partitions.
Please see the Usage section below for an example using partitions.

**Lifetime of a queue and its partitions**

By default, each partition is cleared 24 hours after the last `put` operation.
A lower TTL can be specified by the `partition_ttl` argument in the `put` or `put_many` methods.
Each partition’s expiry is handled independently.

As such, `Queue` s are best used for communication between active functions and not relied on for persistent storage.

On app completion or after stopping an app any associated `Queue` objects are cleaned up.
All its partitions will be cleared.

**Limits**

A single `Queue` can contain up to 100,000 partitions, each with up to 5,000 items. Each item can be up to 256 KiB.

Partition keys must be non-empty and must not exceed 64 bytes.

### hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

### validate\_partition\_key

```
@staticmethod
def validate_partition_key(partition: Optional[str]) -> bytes:
```

Copy

### ephemeral

```
@classmethod
@contextmanager
def ephemeral(
    cls: type["_Queue"],
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    _heartbeat_sleep: float = EPHEMERAL_OBJECT_HEARTBEAT_SLEEP,
) -> Iterator["_Queue"]:
```

Copy

Creates a new ephemeral queue within a context manager:

Usage:

```
from modal import Queue

with Queue.ephemeral() as q:
    q.put(123)
```

Copy

```
async with Queue.ephemeral() as q:
    await q.put.aio(123)
```

Copy

### from\_name

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def from_name(
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
) -> "_Queue":
```

Copy

Reference a named Queue, creating if necessary.

In contrast to `modal.Queue.lookup`, this is a lazy method
the defers hydrating the local object with metadata from
Modal servers until the first time it is actually used.

```
q = modal.Queue.from_name("my-queue", create_if_missing=True)
q.put(123)
```

Copy

### lookup

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def lookup(
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
) -> "_Queue":
```

Copy

Lookup a named Queue.

In contrast to `modal.Queue.from_name`, this is an eager method
that will hydrate the local object with metadata from Modal servers.

```
q = modal.Queue.lookup("my-queue")
q.put(123)
```

Copy

### delete

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def delete(name: str, *, client: Optional[_Client] = None, environment_name: Optional[str] = None):
```

Copy

### clear

```
@live_method
def clear(self, *, partition: Optional[str] = None, all: bool = False) -> None:
```

Copy

Clear the contents of a single partition or all partitions.

### get

```
@live_method
def get(
    self, block: bool = True, timeout: Optional[float] = None, *, partition: Optional[str] = None
) -> Optional[Any]:
```

Copy

Remove and return the next object in the queue.

If `block` is `True` (the default) and the queue is empty, `get` will wait indefinitely for
an object, or until `timeout` if specified. Raises a native `queue.Empty` exception
if the `timeout` is reached.

If `block` is `False`, `get` returns `None` immediately if the queue is empty. The `timeout` is
ignored in this case.

### get\_many

```
@live_method
def get_many(
    self, n_values: int, block: bool = True, timeout: Optional[float] = None, *, partition: Optional[str] = None
) -> list[Any]:
```

Copy

Remove and return up to `n_values` objects from the queue.

If there are fewer than `n_values` items in the queue, return all of them.

If `block` is `True` (the default) and the queue is empty, `get` will wait indefinitely for
at least 1 object to be present, or until `timeout` if specified. Raises the stdlib’s `queue.Empty`
exception if the `timeout` is reached.

If `block` is `False`, `get` returns `None` immediately if the queue is empty. The `timeout` is
ignored in this case.

### put

```
@live_method
def put(
    self,
    v: Any,
    block: bool = True,
    timeout: Optional[float] = None,
    *,
    partition: Optional[str] = None,
    partition_ttl: int = 24 * 3600,  # After 24 hours of no activity, this partition will be deletd.
) -> None:
```

Copy

Add an object to the end of the queue.

If `block` is `True` and the queue is full, this method will retry indefinitely or
until `timeout` if specified. Raises the stdlib’s `queue.Full` exception if the `timeout` is reached.
If blocking it is not recommended to omit the `timeout`, as the operation could wait indefinitely.

If `block` is `False`, this method raises `queue.Full` immediately if the queue is full. The `timeout` is
ignored in this case.

### put\_many

```
@live_method
def put_many(
    self,
    vs: list[Any],
    block: bool = True,
    timeout: Optional[float] = None,
    *,
    partition: Optional[str] = None,
    partition_ttl: int = 24 * 3600,  # After 24 hours of no activity, this partition will be deletd.
) -> None:
```

Copy

Add several objects to the end of the queue.

If `block` is `True` and the queue is full, this method will retry indefinitely or
until `timeout` if specified. Raises the stdlib’s `queue.Full` exception if the `timeout` is reached.
If blocking it is not recommended to omit the `timeout`, as the operation could wait indefinitely.

If `block` is `False`, this method raises `queue.Full` immediately if the queue is full. The `timeout` is
ignored in this case.

### len

```
@live_method
def len(self, *, partition: Optional[str] = None, total: bool = False) -> int:
```

Copy

Return the number of objects in the queue partition.

### iterate

```
@warn_if_generator_is_not_consumed()
@live_method_gen
def iterate(
    self, *, partition: Optional[str] = None, item_poll_timeout: float = 0.0
) -> AsyncGenerator[Any, None]:
```

Copy

(Beta feature) Iterate through items in the queue without mutation.

Specify `item_poll_timeout` to control how long the iterator should wait for the next time before giving up.

[modal.queue](https://modal.com/docs/reference/modal.Queue#modalqueue) [modal.queue.Queue](https://modal.com/docs/reference/modal.Queue#modalqueuequeue) [hydrate](https://modal.com/docs/reference/modal.Queue#hydrate) [validate\_partition\_key](https://modal.com/docs/reference/modal.Queue#validate_partition_key) [ephemeral](https://modal.com/docs/reference/modal.Queue#ephemeral) [from\_name](https://modal.com/docs/reference/modal.Queue#from_name) [lookup](https://modal.com/docs/reference/modal.Queue#lookup) [delete](https://modal.com/docs/reference/modal.Queue#delete) [clear](https://modal.com/docs/reference/modal.Queue#clear) [get](https://modal.com/docs/reference/modal.Queue#get) [get\_many](https://modal.com/docs/reference/modal.Queue#get_many) [put](https://modal.com/docs/reference/modal.Queue#put) [put\_many](https://modal.com/docs/reference/modal.Queue#put_many) [len](https://modal.com/docs/reference/modal.Queue#len) [iterate](https://modal.com/docs/reference/modal.Queue#iterate)

* * *

# modal.Retries

```
class Retries(object)
```

Copy

Adds a retry policy to a Modal function.

**Usage**

```
import modal
app = modal.App()

# Basic configuration.
# This sets a policy of max 4 retries with 1-second delay between failures.
@app.function(retries=4)
def f():
    pass

# Fixed-interval retries with 3-second delay between failures.
@app.function(
    retries=modal.Retries(
        max_retries=2,
        backoff_coefficient=1.0,
        initial_delay=3.0,
    )
)
def g():
    pass

# Exponential backoff, with retry delay doubling after each failure.
@app.function(
    retries=modal.Retries(
        max_retries=4,
        backoff_coefficient=2.0,
        initial_delay=1.0,
    )
)
def h():
    pass
```

Copy

```
def __init__(
    self,
    *,
    # The maximum number of retries that can be made in the presence of failures.
    max_retries: int,
    # Coefficent controlling how much the retry delay increases each retry attempt.
    # A backoff coefficient of 1.0 creates fixed-delay where the delay period always equals the initial delay.
    backoff_coefficient: float = 2.0,
    # Number of seconds that must elapse before the first retry occurs.
    initial_delay: float = 1.0,
    # Maximum length of retry delay in seconds, preventing the delay from growing infinitely.
    max_delay: float = 60.0,
):
```

Copy

Construct a new retries policy, supporting exponential and fixed-interval delays via a backoff coefficient.

[modal.Retries](https://modal.com/docs/reference/modal.Retries#modalretries)

* * *

# modal.sandbox

## modal.sandbox.Sandbox

```
class Sandbox(modal.object.Object)
```

Copy

A `Sandbox` object lets you interact with a running sandbox. This API is similar to Python’s
[asyncio.subprocess.Process](https://docs.python.org/3/library/asyncio-subprocess.html#asyncio.subprocess.Process).

Refer to the [guide](https://modal.com/docs/guide/sandbox) on how to spawn and use sandboxes.

```
def __init__(self, *args, **kwargs):
```

Copy

### hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

### create

```
@staticmethod
def create(
    *entrypoint_args: str,
    app: Optional["modal.app._App"] = None,  # Optionally associate the sandbox with an app
    environment_name: Optional[str] = None,  # Optionally override the default environment
    image: Optional[_Image] = None,  # The image to run as the container for the sandbox.
    mounts: Sequence[_Mount] = (),  # Mounts to attach to the sandbox.
    secrets: Sequence[_Secret] = (),  # Environment variables to inject into the sandbox.
    network_file_systems: dict[Union[str, os.PathLike], _NetworkFileSystem] = {},
    timeout: Optional[int] = None,  # Maximum execution time of the sandbox in seconds.
    workdir: Optional[str] = None,  # Working directory of the sandbox.
    gpu: GPU_T = None,
    cloud: Optional[str] = None,
    region: Optional[Union[str, Sequence[str]]] = None,  # Region or regions to run the sandbox on.
    # Specify, in fractional CPU cores, how many CPU cores to request.
    # Or, pass (request, limit) to additionally specify a hard limit in fractional CPU cores.
    # CPU throttling will prevent a container from exceeding its specified limit.
    cpu: Optional[Union[float, tuple[float, float]]] = None,
    # Specify, in MiB, a memory request which is the minimum memory required.
    # Or, pass (request, limit) to additionally specify a hard limit in MiB.
    memory: Optional[Union[int, tuple[int, int]]] = None,
    block_network: bool = False,  # Whether to block network access
    # List of CIDRs the sandbox is allowed to access. If None, all CIDRs are allowed.
    cidr_allowlist: Optional[Sequence[str]] = None,
    volumes: dict[\
        Union[str, os.PathLike], Union[_Volume, _CloudBucketMount]\
    ] = {},  # Mount points for Modal Volumes and CloudBucketMounts
    pty_info: Optional[api_pb2.PTYInfo] = None,
    # List of ports to tunnel into the sandbox. Encrypted ports are tunneled with TLS.
    encrypted_ports: Sequence[int] = [],
    # List of ports to tunnel into the sandbox without encryption.
    unencrypted_ports: Sequence[int] = [],
    # Reference to a Modal Proxy to use in front of this Sandbox.
    proxy: Optional[_Proxy] = None,
    _experimental_scheduler_placement: Optional[\
        SchedulerPlacement\
    ] = None,  # Experimental controls over fine-grained scheduling (alpha).
    client: Optional[_Client] = None,
) -> "_Sandbox":
```

Copy

### from\_id

```
@staticmethod
def from_id(sandbox_id: str, client: Optional[_Client] = None) -> "_Sandbox":
```

Copy

Construct a Sandbox from an id and look up the Sandbox result.

The ID of a Sandbox object can be accessed using `.object_id`.

### set\_tags

```
def set_tags(self, tags: dict[str, str], *, client: Optional[_Client] = None):
```

Copy

Set tags (key-value pairs) on the Sandbox. Tags can be used to filter results in `Sandbox.list`.

### snapshot\_filesystem

```
def snapshot_filesystem(self, timeout: int = 55) -> _Image:
```

Copy

Snapshot the filesystem of the Sandbox.

Returns an [`Image`](https://modal.com/docs/reference/modal.Image) object which
can be used to spawn a new Sandbox with the same filesystem.

### wait

```
def wait(self, raise_on_termination: bool = True):
```

Copy

Wait for the Sandbox to finish running.

### tunnels

```
def tunnels(self, timeout: int = 50) -> dict[int, Tunnel]:
```

Copy

Get tunnel metadata for the sandbox.

Raises `SandboxTimeoutError` if the tunnels are not available after the timeout.

Returns a dictionary of `Tunnel` objects which are keyed by the container port.

NOTE: Previous to client v0.64.152, this returned a list of `TunnelData` objects.

### terminate

```
def terminate(self):
```

Copy

Terminate Sandbox execution.

This is a no-op if the Sandbox has already finished running.

### poll

```
def poll(self) -> Optional[int]:
```

Copy

Check if the Sandbox has finished running.

Returns `None` if the Sandbox is still running, else returns the exit code.

### exec

```
def exec(
    self,
    *cmds: str,
    pty_info: Optional[api_pb2.PTYInfo] = None,  # Deprecated: internal use only
    stdout: StreamType = StreamType.PIPE,
    stderr: StreamType = StreamType.PIPE,
    timeout: Optional[int] = None,
    workdir: Optional[str] = None,
    secrets: Sequence[_Secret] = (),
    # Encode output as text.
    text: bool = True,
    # Control line-buffered output.
    # -1 means unbuffered, 1 means line-buffered (only available if `text=True`).
    bufsize: Literal[-1, 1] = -1,
    # Internal option to set terminal size and metadata
    _pty_info: Optional[api_pb2.PTYInfo] = None,
):
```

Copy

Execute a command in the Sandbox and return
a [`ContainerProcess`](https://modal.com/docs/reference/modal.ContainerProcess#modalcontainer_process) handle.

**Usage**

```
app = modal.App.lookup("my-app", create_if_missing=True)

sandbox = modal.Sandbox.create("sleep", "infinity", app=app)

process = sandbox.exec("bash", "-c", "for i in $(seq 1 10); do echo foo $i; sleep 0.5; done")

for line in process.stdout:
    print(line)
```

Copy

### open

```
def open(
    self,
    path: str,
    mode: Union["_typeshed.OpenTextMode", "_typeshed.OpenBinaryMode"] = "r",
):
```

Copy

Open a file in the Sandbox and return
a [`FileIO`](https://modal.com/docs/reference/modal.FileIO#modalfile_io) handle.

**Usage**

```
sb = modal.Sandbox.create(app=sb_app)
f = sb.open("/test.txt", "w")
f.write("hello")
f.close()
```

Copy

### ls

```
def ls(self, path: str) -> list[str]:
```

Copy

List the contents of a directory in the Sandbox.

### mkdir

```
def mkdir(self, path: str, parents: bool = False) -> None:
```

Copy

Create a new directory in the Sandbox.

### rm

```
def rm(self, path: str, recursive: bool = False) -> None:
```

Copy

Remove a file or directory in the Sandbox.

### watch

```
def watch(
    self,
    path: str,
    filter: Optional[list[FileWatchEventType]] = None,
    recursive: Optional[bool] = None,
    timeout: Optional[int] = None,
) -> Iterator[FileWatchEvent]:
```

Copy

### stdout

```
@property
def stdout(self) -> _StreamReader[str]:
```

Copy

[`StreamReader`](https://modal.com/docs/reference/modal.io_streams#modalio_streamsstreamreader) for
the sandbox’s stdout stream.

### stderr

```
@property
def stderr(self) -> _StreamReader[str]:
```

Copy

[`StreamReader`](https://modal.com/docs/reference/modal.io_streams#modalio_streamsstreamreader) for
the sandbox’s stderr stream.

### stdin

```
@property
def stdin(self) -> _StreamWriter:
```

Copy

[`StreamWriter`](https://modal.com/docs/reference/modal.io_streams#modalio_streamsstreamwriter) for
the sandbox’s stdin stream.

### returncode

```
@property
def returncode(self) -> Optional[int]:
```

Copy

Return code of the sandbox process if it has finished running, else `None`.

### list

```
@staticmethod
def list(
    *, app_id: Optional[str] = None, tags: Optional[dict[str, str]] = None, client: Optional[_Client] = None
) -> AsyncGenerator["_Sandbox", None]:
```

Copy

List all sandboxes for the current environment or app ID (if specified). If tags are specified, only
sandboxes that have at least those tags are returned. Returns an iterator over `Sandbox` objects.

[modal.sandbox](https://modal.com/docs/reference/modal.Sandbox#modalsandbox) [modal.sandbox.Sandbox](https://modal.com/docs/reference/modal.Sandbox#modalsandboxsandbox) [hydrate](https://modal.com/docs/reference/modal.Sandbox#hydrate) [create](https://modal.com/docs/reference/modal.Sandbox#create) [from\_id](https://modal.com/docs/reference/modal.Sandbox#from_id) [set\_tags](https://modal.com/docs/reference/modal.Sandbox#set_tags) [snapshot\_filesystem](https://modal.com/docs/reference/modal.Sandbox#snapshot_filesystem) [wait](https://modal.com/docs/reference/modal.Sandbox#wait) [tunnels](https://modal.com/docs/reference/modal.Sandbox#tunnels) [terminate](https://modal.com/docs/reference/modal.Sandbox#terminate) [poll](https://modal.com/docs/reference/modal.Sandbox#poll) [exec](https://modal.com/docs/reference/modal.Sandbox#exec) [open](https://modal.com/docs/reference/modal.Sandbox#open) [ls](https://modal.com/docs/reference/modal.Sandbox#ls) [mkdir](https://modal.com/docs/reference/modal.Sandbox#mkdir) [rm](https://modal.com/docs/reference/modal.Sandbox#rm) [watch](https://modal.com/docs/reference/modal.Sandbox#watch) [stdout](https://modal.com/docs/reference/modal.Sandbox#stdout) [stderr](https://modal.com/docs/reference/modal.Sandbox#stderr) [stdin](https://modal.com/docs/reference/modal.Sandbox#stdin) [returncode](https://modal.com/docs/reference/modal.Sandbox#returncode) [list](https://modal.com/docs/reference/modal.Sandbox#list)

* * *

# modal.secret

## modal.secret.Secret

```
class Secret(modal.object.Object)
```

Copy

Secrets provide a dictionary of environment variables for images.

Secrets are a secure way to add credentials and other sensitive information
to the containers your functions run in. You can create and edit secrets on
[the dashboard](https://modal.com/secrets), or programmatically from Python code.

See [the secrets guide page](https://modal.com/docs/guide/secrets) for more information.

```
def __init__(self, *args, **kwargs):
```

Copy

### hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

### from\_dict

```
@staticmethod
def from_dict(
    env_dict: dict[\
        str, Union[str, None]\
    ] = {},  # dict of entries to be inserted as environment variables in functions using the secret
):
```

Copy

Create a secret from a str-str dictionary. Values can also be `None`, which is ignored.

Usage:

```
@app.function(secrets=[modal.Secret.from_dict({"FOO": "bar"})])
def run():
    print(os.environ["FOO"])
```

Copy

### from\_local\_environ

```
@staticmethod
def from_local_environ(
    env_keys: list[str],  # list of local env vars to be included for remote execution
):
```

Copy

Create secrets from local environment variables automatically.

### from\_dotenv

```
@staticmethod
def from_dotenv(path=None, *, filename=".env"):
```

Copy

Create secrets from a .env file automatically.

If no argument is provided, it will use the current working directory as the starting
point for finding a `.env` file. Note that it does not use the location of the module
calling `Secret.from_dotenv`.

If called with an argument, it will use that as a starting point for finding `.env` files.
In particular, you can call it like this:

```
@app.function(secrets=[modal.Secret.from_dotenv(__file__)])
def run():
    print(os.environ["USERNAME"])  # Assumes USERNAME is defined in your .env file
```

Copy

This will use the location of the script calling `modal.Secret.from_dotenv` as a
starting point for finding the `.env` file.

A file named `.env` is expected by default, but this can be overridden with the `filename`
keyword argument:

```
@app.function(secrets=[modal.Secret.from_dotenv(filename=".env-dev")])
def run():
    ...
```

Copy

### from\_name

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def from_name(
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    environment_name: Optional[str] = None,
    required_keys: list[\
        str\
    ] = [],  # Optionally, a list of required environment variables (will be asserted server-side)
) -> "_Secret":
```

Copy

Reference a Secret by its name.

In contrast to most other Modal objects, named Secrets must be provisioned
from the Dashboard. See other methods for alternate ways of creating a new
Secret from code.

```
secret = modal.Secret.from_name("my-secret")

@app.function(secrets=[secret])
def run():
   ...
```

Copy

[modal.secret](https://modal.com/docs/reference/modal.Secret#modalsecret) [modal.secret.Secret](https://modal.com/docs/reference/modal.Secret#modalsecretsecret) [hydrate](https://modal.com/docs/reference/modal.Secret#hydrate) [from\_dict](https://modal.com/docs/reference/modal.Secret#from_dict) [from\_local\_environ](https://modal.com/docs/reference/modal.Secret#from_local_environ) [from\_dotenv](https://modal.com/docs/reference/modal.Secret#from_dotenv) [from\_name](https://modal.com/docs/reference/modal.Secret#from_name)

* * *

# modal.Tunnel

```
class Tunnel(object)
```

Copy

A port forwarded from within a running Modal container. Created by `modal.forward()`.

**Important:** This is an experimental API which may change in the future.

```
def __init__(self, host: str, port: int, unencrypted_host: str, unencrypted_port: int) -> None
```

Copy

## url

```
@property
def url(self) -> str:
```

Copy

Get the public HTTPS URL of the forwarded port.

## tls\_socket

```
@property
def tls_socket(self) -> tuple[str, int]:
```

Copy

Get the public TLS socket as a (host, port) tuple.

## tcp\_socket

```
@property
def tcp_socket(self) -> tuple[str, int]:
```

Copy

Get the public TCP socket as a (host, port) tuple.

[modal.Tunnel](https://modal.com/docs/reference/modal.Tunnel#modaltunnel) [url](https://modal.com/docs/reference/modal.Tunnel#url) [tls\_socket](https://modal.com/docs/reference/modal.Tunnel#tls_socket) [tcp\_socket](https://modal.com/docs/reference/modal.Tunnel#tcp_socket)

* * *

# modal.Volume

```
class Volume(modal.object.Object)
```

Copy

A writeable volume that can be used to share files between one or more Modal functions.

The contents of a volume is exposed as a filesystem. You can use it to share data between different functions, or
to persist durable state across several instances of the same function.

Unlike a networked filesystem, you need to explicitly reload the volume to see changes made since it was mounted.
Similarly, you need to explicitly commit any changes you make to the volume for the changes to become visible
outside the current container.

Concurrent modification is supported, but concurrent modifications of the same files should be avoided! Last write
wins in case of concurrent modification of the same file - any data the last writer didn’t have when committing
changes will be lost!

As a result, volumes are typically not a good fit for use cases where you need to make concurrent modifications to
the same file (nor is distributed file locking supported).

Volumes can only be reloaded if there are no open files for the volume - attempting to reload with open files
will result in an error.

**Usage**

```
import modal

app = modal.App()
volume = modal.Volume.from_name("my-persisted-volume", create_if_missing=True)

@app.function(volumes={"/root/foo": volume})
def f():
    with open("/root/foo/bar.txt", "w") as f:
        f.write("hello")
    volume.commit()  # Persist changes

@app.function(volumes={"/root/foo": volume})
def g():
    volume.reload()  # Fetch latest changes
    with open("/root/foo/bar.txt", "r") as f:
        print(f.read())
```

Copy

```
def __init__(self, *args, **kwargs):
```

Copy

## hydrate

```
def hydrate(self, client: Optional[_Client] = None) -> Self:
```

Copy

Synchronize the local object with its identity on the Modal server.

It is rarely necessary to call this method explicitly, as most operations
will lazily hydrate when needed. The main use case is when you need to
access object metadata, such as its ID.

## from\_name

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def from_name(
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
    version: "typing.Optional[modal_proto.api_pb2.VolumeFsVersion.ValueType]" = None,
) -> "_Volume":
```

Copy

Reference a Volume by name, creating if necessary.

In contrast to `modal.Volume.lookup`, this is a lazy method
that defers hydrating the local object with metadata from
Modal servers until the first time is is actually used.

```
vol = modal.Volume.from_name("my-volume", create_if_missing=True)

app = modal.App()

# Volume refers to the same object, even across instances of `app`.
@app.function(volumes={"/data": vol})
def f():
    pass
```

Copy

## ephemeral

```
@classmethod
@contextmanager
def ephemeral(
    cls: type["_Volume"],
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    version: "typing.Optional[modal_proto.api_pb2.VolumeFsVersion.ValueType]" = None,
    _heartbeat_sleep: float = EPHEMERAL_OBJECT_HEARTBEAT_SLEEP,
) -> AsyncGenerator["_Volume", None]:
```

Copy

Creates a new ephemeral volume within a context manager:

Usage:

```
import modal
with modal.Volume.ephemeral() as vol:
    assert vol.listdir("/") == []
```

Copy

```
async with modal.Volume.ephemeral() as vol:
    assert await vol.listdir("/") == []
```

Copy

## lookup

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def lookup(
    name: str,
    namespace=api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    create_if_missing: bool = False,
    version: "typing.Optional[modal_proto.api_pb2.VolumeFsVersion.ValueType]" = None,
) -> "_Volume":
```

Copy

Lookup a named Volume.

In contrast to `modal.Volume.from_name`, this is an eager method
that will hydrate the local object with metadata from Modal servers.

```
vol = modal.Volume.lookup("my-volume")
print(vol.listdir("/"))
```

Copy

## commit

```
@live_method
def commit(self):
```

Copy

Commit changes to the volume.

If successful, the changes made are now persisted in durable storage and available to other containers accessing
the volume.

## reload

```
@live_method
def reload(self):
```

Copy

Make latest committed state of volume available in the running container.

Any uncommitted changes to the volume, such as new or modified files, may implicitly be committed when
reloading.

Reloading will fail if there are open files for the volume.

## iterdir

```
@live_method_gen
def iterdir(self, path: str, *, recursive: bool = True) -> Iterator[FileEntry]:
```

Copy

Iterate over all files in a directory in the volume.

Passing a directory path lists all files in the directory. For a file path, return only that
file’s description. If `recursive` is set to True, list all files and folders under the path
recursively.

## listdir

```
@live_method
def listdir(self, path: str, *, recursive: bool = False) -> list[FileEntry]:
```

Copy

List all files under a path prefix in the modal.Volume.

Passing a directory path lists all files in the directory. For a file path, return only that
file’s description. If `recursive` is set to True, list all files and folders under the path
recursively.

## read\_file

```
@live_method_gen
def read_file(self, path: str) -> Iterator[bytes]:
```

Copy

Read a file from the modal.Volume.

**Example:**

```
vol = modal.Volume.lookup("my-modal-volume")
data = b""
for chunk in vol.read_file("1mb.csv"):
    data += chunk
print(len(data))  # == 1024 * 1024
```

Copy

## remove\_file

```
@live_method
def remove_file(self, path: str, recursive: bool = False) -> None:
```

Copy

Remove a file or directory from a volume.

## copy\_files

```
@live_method
def copy_files(self, src_paths: Sequence[str], dst_path: str) -> None:
```

Copy

Copy files within the volume from src\_paths to dst\_path.
The semantics of the copy operation follow those of the UNIX cp command.

The `src_paths` parameter is a list. If you want to copy a single file, you should pass a list with a
single element.

`src_paths` and `dst_path` should refer to the desired location _inside_ the volume. You do not need to prepend
the volume mount path.

**Usage**

```
vol = modal.Volume.lookup("my-modal-volume")

vol.copy_files(["bar/example.txt"], "bar2")  # Copy files to another directory
vol.copy_files(["bar/example.txt"], "bar/example2.txt")  # Rename a file by copying
```

Copy

Note that if the volume is already mounted on the Modal function, you should use normal filesystem operations
like `os.rename()` and then `commit()` the volume. The `copy_files()` method is useful when you don’t have
the volume mounted as a filesystem, e.g. when running a script on your local computer.

## batch\_upload

```
@live_method
def batch_upload(self, force: bool = False) -> "_VolumeUploadContextManager":
```

Copy

Initiate a batched upload to a volume.

To allow overwriting existing files, set `force` to `True` (you cannot overwrite existing directories with
uploaded files regardless).

**Example:**

```
vol = modal.Volume.lookup("my-modal-volume")

with vol.batch_upload() as batch:
    batch.put_file("local-path.txt", "/remote-path.txt")
    batch.put_directory("/local/directory/", "/remote/directory")
    batch.put_file(io.BytesIO(b"some data"), "/foobar")
```

Copy

## delete

```
@staticmethod
@renamed_parameter((2024, 12, 18), "label", "name")
def delete(name: str, client: Optional[_Client] = None, environment_name: Optional[str] = None):
```

Copy

## rename

```
@staticmethod
def rename(
    old_name: str,
    new_name: str,
    *,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
):
```

Copy

[modal.Volume](https://modal.com/docs/reference/modal.Volume#modalvolume) [hydrate](https://modal.com/docs/reference/modal.Volume#hydrate) [from\_name](https://modal.com/docs/reference/modal.Volume#from_name) [ephemeral](https://modal.com/docs/reference/modal.Volume#ephemeral) [lookup](https://modal.com/docs/reference/modal.Volume#lookup) [commit](https://modal.com/docs/reference/modal.Volume#commit) [reload](https://modal.com/docs/reference/modal.Volume#reload) [iterdir](https://modal.com/docs/reference/modal.Volume#iterdir) [listdir](https://modal.com/docs/reference/modal.Volume#listdir) [read\_file](https://modal.com/docs/reference/modal.Volume#read_file) [remove\_file](https://modal.com/docs/reference/modal.Volume#remove_file) [copy\_files](https://modal.com/docs/reference/modal.Volume#copy_files) [batch\_upload](https://modal.com/docs/reference/modal.Volume#batch_upload) [delete](https://modal.com/docs/reference/modal.Volume#delete) [rename](https://modal.com/docs/reference/modal.Volume#rename)

* * *

# modal.asgi\_app

```
def asgi_app(
    _warn_parentheses_missing=None,
    *,
    label: Optional[str] = None,  # Label for created endpoint. Final subdomain will be --.modal.run.
    custom_domains: Optional[Iterable[str]] = None,  # Deploy this endpoint on a custom domain.
    requires_proxy_auth: bool = False,  # Require Proxy-Authorization HTTP Headers on requests
    wait_for_response: bool = True,  # DEPRECATED: this must always be True now
) -> Callable[[Callable[..., Any]], _PartialFunction]:
```

Copy

Decorator for registering an ASGI app with a Modal function.

Asynchronous Server Gateway Interface (ASGI) is a standard for Python
synchronous and asynchronous apps, supported by all popular Python web
libraries. This is an advanced decorator that gives full flexibility in
defining one or more web endpoints on Modal.

**Usage:**

```
from typing import Callable

@app.function()
@modal.asgi_app()
def create_asgi() -> Callable:
    ...
```

Copy

To learn how to use Modal with popular web frameworks, see the
[guide on web endpoints](https://modal.com/docs/guide/webhooks).

[modal.asgi\_app](https://modal.com/docs/reference/modal.asgi_app#modalasgi_app)






* * *

# modal.batched

```
def batched(
    _warn_parentheses_missing=None,
    *,
    max_batch_size: int,
    wait_ms: int,
) -> Callable[[Callable[..., Any]], _PartialFunction]:
```

Copy

Decorator for functions or class methods that should be batched.

**Usage**

```
@app.function()
@modal.batched(max_batch_size=4, wait_ms=1000)
async def batched_multiply(xs: list[int], ys: list[int]) -> list[int]:
    return [x * y for x, y in zip(xs, xs)]

# call batched_multiply with individual inputs
batched_multiply.remote.aio(2, 100)
```

Copy

See the [dynamic batching guide](https://modal.com/docs/guide/dynamic-batching) for more information.

[modal.batched](https://modal.com/docs/reference/modal.batched#modalbatched)






* * *

# modal.build

```
def build(
    _warn_parentheses_missing=None, *, force: bool = False, timeout: int = 86400
) -> Callable[[Union[Callable[[Any], Any], _PartialFunction]], _PartialFunction]:
```

Copy

Decorator for methods that execute at _build time_ to create a new Image layer.

**Deprecated**: This function is deprecated. We recommend using `modal.Volume`
to store large assets (such as model weights) instead of writing them to the
Image during the build process. For other use cases, you can replace this
decorator with the `Image.run_function` method.

**Usage**

```
@app.cls(gpu="A10G")
class AlpacaLoRAModel:
    @build()
    def download_models(self):
        model = LlamaForCausalLM.from_pretrained(
            base_model,
        )
        PeftModel.from_pretrained(model, lora_weights)
        LlamaTokenizer.from_pretrained(base_model)
```

Copy

[modal.build](https://modal.com/docs/reference/modal.build#modalbuild)






* * *

# modal.call\_graph

## modal.call\_graph.InputInfo

```
class InputInfo(object)
```

Copy

Simple data structure storing information about a function input.

```
def __init__(self, input_id: str, function_call_id: str, task_id: str, status: modal.call_graph.InputStatus, function_name: str, module_name: str, children: list['InputInfo']) -> None
```

Copy

## modal.call\_graph.InputStatus

```
class InputStatus(enum.IntEnum)
```

Copy

Enum representing status of a function input.

The possible values are:

- `PENDING`
- `SUCCESS`
- `FAILURE`
- `INIT_FAILURE`
- `TERMINATED`
- `TIMEOUT`

[modal.call\_graph](https://modal.com/docs/reference/modal.call_graph#modalcall_graph) [modal.call\_graph.InputInfo](https://modal.com/docs/reference/modal.call_graph#modalcall_graphinputinfo) [modal.call\_graph.InputStatus](https://modal.com/docs/reference/modal.call_graph#modalcall_graphinputstatus)






* * *

# modal.current\_function\_call\_id

```
def current_function_call_id() -> Optional[str]:
```

Copy

Returns the function call ID for the current input.

Can only be called from Modal function (i.e. in a container context).

```
from modal import current_function_call_id

@app.function()
def process_stuff():
    print(f"Starting to process input from {current_function_call_id()}")
```

Copy

[modal.current\_function\_call\_id](https://modal.com/docs/reference/modal.current_function_call_id#modalcurrent_function_call_id)






* * *

# modal.current\_input\_id

```
def current_input_id() -> Optional[str]:
```

Copy

Returns the input ID for the current input.

Can only be called from Modal function (i.e. in a container context).

```
from modal import current_input_id

@app.function()
def process_stuff():
    print(f"Starting to process {current_input_id()}")
```

Copy

[modal.current\_input\_id](https://modal.com/docs/reference/modal.current_input_id#modalcurrent_input_id)






* * *

# modal.enable\_output

```
@contextlib.contextmanager
def enable_output(show_progress: bool = True) -> Generator[None, None, None]:
```

Copy

Context manager that enable output when using the Python SDK.

This will print to stdout and stderr things such as

1. Logs from running functions
2. Status of creating objects
3. Map progress

Example:

```
app = modal.App()
with modal.enable_output():
    with app.run():
        ...
```

Copy

[modal.enable\_output](https://modal.com/docs/reference/modal.enable_output#modalenable_output)






* * *

# modal.enter

```
def enter(
    _warn_parentheses_missing=None,
    *,
    snap: bool = False,
) -> Callable[[Union[Callable[[Any], Any], _PartialFunction]], _PartialFunction]:
```

Copy

Decorator for methods which should be executed when a new container is started.

See the [lifeycle function guide](https://modal.com/docs/guide/lifecycle-functions#enter) for more information.

[modal.enter](https://modal.com/docs/reference/modal.enter#modalenter)






* * *

# modal.exit

```
def exit(_warn_parentheses_missing=None) -> Callable[[ExitHandlerType], _PartialFunction]:
```

Copy

Decorator for methods which should be executed when a container is about to exit.

See the [lifeycle function guide](https://modal.com/docs/guide/lifecycle-functions#exit) for more information.

[modal.exit](https://modal.com/docs/reference/modal.exit#modalexit)






* * *

# modal.forward

```
@contextmanager
def forward(port: int, *, unencrypted: bool = False, client: Optional[_Client] = None) -> Iterator[Tunnel]:
```

Copy

Expose a port publicly from inside a running Modal container, with TLS.

If `unencrypted` is set, this also exposes the TCP socket without encryption on a random port
number. This can be used to SSH into a container (see example below). Note that it is on the public Internet, so
make sure you are using a secure protocol over TCP.

**Important:** This is an experimental API which may change in the future.

**Usage:**

```
import modal
from flask import Flask

app = modal.App(image=modal.Image.debian_slim().pip_install("Flask"))
flask_app = Flask(__name__)

@flask_app.route("/")
def hello_world():
    return "Hello, World!"

@app.function()
def run_app():
    # Start a web server inside the container at port 8000. `modal.forward(8000)` lets us
    # expose that port to the world at a random HTTPS URL.
    with modal.forward(8000) as tunnel:
        print("Server listening at", tunnel.url)
        flask_app.run("0.0.0.0", 8000)

    # When the context manager exits, the port is no longer exposed.
```

Copy

**Raw TCP usage:**

```
import socket
import threading

import modal

def run_echo_server(port: int):
    """Run a TCP echo server listening on the given port."""
    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.bind(("0.0.0.0", port))
    sock.listen(1)

    while True:
        conn, addr = sock.accept()
        print("Connection from:", addr)

        # Start a new thread to handle the connection
        def handle(conn):
            with conn:
                while True:
                    data = conn.recv(1024)
                    if not data:
                        break
                    conn.sendall(data)

        threading.Thread(target=handle, args=(conn,)).start()

app = modal.App()

@app.function()
def tcp_tunnel():
    # This exposes port 8000 to public Internet traffic over TCP.
    with modal.forward(8000, unencrypted=True) as tunnel:
        # You can connect to this TCP socket from outside the container, for example, using `nc`:
        #  nc  
        print("TCP tunnel listening at:", tunnel.tcp_socket)
        run_echo_server(8000)
```

Copy

**SSH example:**
This assumes you have a rsa keypair in `~/.ssh/id_rsa{.pub}`, this is a bare-bones example
letting you SSH into a Modal container.

```
import subprocess
import time

import modal

app = modal.App()
image = (
    modal.Image.debian_slim()
    .apt_install("openssh-server")
    .run_commands("mkdir /run/sshd")
    .add_local_file("~/.ssh/id_rsa.pub", "/root/.ssh/authorized_keys", copy=True)
)

@app.function(image=image, timeout=3600)
def some_function():
    subprocess.Popen(["/usr/sbin/sshd", "-D", "-e"])
    with modal.forward(port=22, unencrypted=True) as tunnel:
        hostname, port = tunnel.tcp_socket
        connection_cmd = f'ssh -p {port} root@{hostname}'
        print(f"ssh into container using: {connection_cmd}")
        time.sleep(3600)  # keep alive for 1 hour or until killed
```

Copy

If you intend to use this more generally, a suggestion is to put the subprocess and port
forwarding code in an `@enter` lifecycle method of an @app.cls, to only make a single
ssh server and port for each container (and not one for each input to the function).

[modal.forward](https://modal.com/docs/reference/modal.forward#modalforward)






* * *

# modal.gpu

**GPU configuration shortcodes**

The following are the valid `str` values for the `gpu` parameter of
[`@app.function`](https://modal.com/docs/reference/modal.App#function).

- “t4” → `GPU(T4, count=1)`
- “l4” → `GPU(L4, count=1)`
- “a100” → `GPU(A100-40GB, count=1)`
- “a100-80gb” → `GPU(A100-80GB, count=1)`
- “h100” → `GPU(H100, count=1)`
- “a10g” → `GPU(A10G, count=1)`
- “l40s” → `GPU(L40S, count=1)`
- “any” → `GPU(Any, count=1)`

The shortcodes also support specifying count by suffixing `:N` to acquire `N` GPUs.
For example, `a10g:4` will provision 4 A10G GPUs.

Other configurations can be created using the constructors documented below.

## modal.gpu.A100

```
class A100(modal.gpu._GPUConfig)
```

Copy

[NVIDIA A100 Tensor Core](https://www.nvidia.com/en-us/data-center/a100/) GPU class.

The flagship data center GPU of the Ampere architecture. Available in 40GB and 80GB GPU memory configurations.

```
def __init__(
    self,
    *,
    count: int = 1,  # Number of GPUs per container. Defaults to 1.
    size: Union[str, None] = None,  # Select GB configuration of GPU device: "40GB" or "80GB". Defaults to "40GB".
):
```

Copy

## modal.gpu.A10G

```
class A10G(modal.gpu._GPUConfig)
```

Copy

[NVIDIA A10G Tensor Core](https://www.nvidia.com/en-us/data-center/products/a10-gpu/) GPU class.

A mid-tier data center GPU based on the Ampere architecture, providing 24 GB of memory.
A10G GPUs deliver up to 3.3x better ML training performance, 3x better ML inference performance,
and 3x better graphics performance, in comparison to NVIDIA T4 GPUs.

```
def __init__(
    self,
    *,
    # Number of GPUs per container. Defaults to 1.
    # Useful if you have very large models that don't fit on a single GPU.
    count: int = 1,
):
```

Copy

## modal.gpu.Any

```
class Any(modal.gpu._GPUConfig)
```

Copy

Selects any one of the GPU classes available within Modal, according to availability.

```
def __init__(self, *, count: int = 1):
```

Copy

## modal.gpu.H100

```
class H100(modal.gpu._GPUConfig)
```

Copy

[NVIDIA H100 Tensor Core](https://www.nvidia.com/en-us/data-center/h100/) GPU class.

The flagship data center GPU of the Hopper architecture.
Enhanced support for FP8 precision and a Transformer Engine that provides up to 4X faster training
over the prior generation for GPT-3 (175B) models.

```
def __init__(
    self,
    *,
    # Number of GPUs per container. Defaults to 1.
    # Useful if you have very large models that don't fit on a single GPU.
    count: int = 1,
):
```

Copy

## modal.gpu.L4

```
class L4(modal.gpu._GPUConfig)
```

Copy

[NVIDIA L4 Tensor Core](https://www.nvidia.com/en-us/data-center/l4/) GPU class.

A mid-tier data center GPU based on the Ada Lovelace architecture, providing 24GB of GPU memory.
Includes RTX (ray tracing) support.

```
def __init__(
    self,
    count: int = 1,  # Number of GPUs per container. Defaults to 1.
):
```

Copy

## modal.gpu.L40S

```
class L40S(modal.gpu._GPUConfig)
```

Copy

[NVIDIA L40S](https://www.nvidia.com/en-us/data-center/l40s/) GPU class.

The L40S is a data center GPU for the Ada Lovelace architecture. It has 48 GB of on-chip
GDDR6 RAM and enhanced support for FP8 precision.

```
def __init__(
    self,
    *,
    # Number of GPUs per container. Defaults to 1.
    # Useful if you have very large models that don't fit on a single GPU.
    count: int = 1,
):
```

Copy

## modal.gpu.T4

```
class T4(modal.gpu._GPUConfig)
```

Copy

[NVIDIA T4 Tensor Core](https://www.nvidia.com/en-us/data-center/tesla-t4/) GPU class.

A low-cost data center GPU based on the Turing architecture, providing 16GB of GPU memory.

```
def __init__(
    self,
    count: int = 1,  # Number of GPUs per container. Defaults to 1.
):
```

Copy

[modal.gpu](https://modal.com/docs/reference/modal.gpu#modalgpu) [modal.gpu.A100](https://modal.com/docs/reference/modal.gpu#modalgpua100) [modal.gpu.A10G](https://modal.com/docs/reference/modal.gpu#modalgpua10g) [modal.gpu.Any](https://modal.com/docs/reference/modal.gpu#modalgpuany) [modal.gpu.H100](https://modal.com/docs/reference/modal.gpu#modalgpuh100) [modal.gpu.L4](https://modal.com/docs/reference/modal.gpu#modalgpul4) [modal.gpu.L40S](https://modal.com/docs/reference/modal.gpu#modalgpul40s) [modal.gpu.T4](https://modal.com/docs/reference/modal.gpu#modalgput4)






* * *

# modal.interact

```
def interact() -> None:
```

Copy

Enable interactivity with user input inside a Modal container.

See the [interactivity guide](https://modal.com/docs/guide/developing-debugging#interactivity)
for more information on how to use this function.

[modal.interact](https://modal.com/docs/reference/modal.interact#modalinteract)






* * *

# modal.io\_streams

## modal.io\_streams.StreamReader

```
class StreamReader(typing.Generic)
```

Copy

Retrieve logs from a stream ( `stdout` or `stderr`).

As an asynchronous iterable, the object supports the `for` and `async for`
statements. Just loop over the object to read in chunks.

**Usage**

```
from modal import Sandbox

sandbox = Sandbox.create(
    "bash",
    "-c",
    "for i in $(seq 1 10); do echo foo; sleep 0.1; done",
    app=app,
)
for message in sandbox.stdout:
    print(f"Message: {message}")
```

Copy

### file\_descriptor

```
@property
def file_descriptor(self) -> int:
```

Copy

Possible values are `1` for stdout and `2` for stderr.

### read

```
def read(self) -> T:
```

Copy

Fetch the entire contents of the stream until EOF.

**Usage**

```
from modal import Sandbox

sandbox = Sandbox.create("echo", "hello", app=app)
sandbox.wait()

print(sandbox.stdout.read())
```

Copy

## modal.io\_streams.StreamWriter

```
class StreamWriter(object)
```

Copy

Provides an interface to buffer and write logs to a sandbox or container process stream ( `stdin`).

### write

```
def write(self, data: Union[bytes, bytearray, memoryview, str]) -> None:
```

Copy

Write data to the stream but does not send it immediately.

This is non-blocking and queues the data to an internal buffer. Must be
used along with the `drain()` method, which flushes the buffer.

**Usage**

```
from modal import Sandbox

sandbox = Sandbox.create(
    "bash",
    "-c",
    "while read line; do echo $line; done",
    app=app,
)
sandbox.stdin.write(b"foo\n")
sandbox.stdin.write(b"bar\n")
sandbox.stdin.write_eof()

sandbox.stdin.drain()
sandbox.wait()
```

Copy

### write\_eof

```
def write_eof(self) -> None:
```

Copy

Close the write end of the stream after the buffered data is drained.

If the process was blocked on input, it will become unblocked after
`write_eof()`. This method needs to be used along with the `drain()`
method, which flushes the EOF to the process.

### drain

```
def drain(self) -> None:
```

Copy

Flush the write buffer and send data to the running process.

This is a flow control method that blocks until data is sent. It returns
when it is appropriate to continue writing data to the stream.

**Usage**

```
writer.write(data)
writer.drain()
```

Copy

Async usage:

```
writer.write(data)  # not a blocking operation
await writer.drain.aio()
```

Copy

[modal.io\_streams](https://modal.com/docs/reference/modal.io_streams#modalio_streams) [modal.io\_streams.StreamReader](https://modal.com/docs/reference/modal.io_streams#modalio_streamsstreamreader) [file\_descriptor](https://modal.com/docs/reference/modal.io_streams#file_descriptor) [read](https://modal.com/docs/reference/modal.io_streams#read) [modal.io\_streams.StreamWriter](https://modal.com/docs/reference/modal.io_streams#modalio_streamsstreamwriter) [write](https://modal.com/docs/reference/modal.io_streams#write) [write\_eof](https://modal.com/docs/reference/modal.io_streams#write_eof) [drain](https://modal.com/docs/reference/modal.io_streams#drain)






* * *

# modal.is\_local

```
def is_local() -> bool:
```

Copy

Returns if we are currently on the machine launching/deploying a Modal app

Returns `True` when executed locally on the user’s machine.
Returns `False` when executed from a Modal container in the cloud.

[modal.is\_local](https://modal.com/docs/reference/modal.is_local#modalis_local)






* * *

# modal.method

```
def method(
    _warn_parentheses_missing=None,
    *,
    # Set this to True if it's a non-generator function returning
    # a [sync/async] generator object
    is_generator: Optional[bool] = None,
    keep_warm: Optional[int] = None,  # Deprecated: Use keep_warm on @app.cls() instead
) -> _MethodDecoratorType:
```

Copy

Decorator for methods that should be transformed into a Modal Function registered against this class’s App.

**Usage:**

```
@app.cls(cpu=8)
class MyCls:

    @modal.method()
    def f(self):
        ...
```

Copy

[modal.method](https://modal.com/docs/reference/modal.method#modalmethod)






* * *

# modal.parameter

```
def parameter(*, default: Any = _no_default, init: bool = True) -> Any:
```

Copy

Used to specify options for modal.cls parameters, similar to dataclass.field for dataclasses

```
class A:
    a: str = modal.parameter()
```

Copy

If `init=False` is specified, the field is not considered a parameter for the
Modal class and not used in the synthesized constructor. This can be used to
optionally annotate the type of a field that’s used internally, for example values
being set by @enter lifecycle methods, without breaking type checkers, but it has
no runtime effect on the class.

[modal.parameter](https://modal.com/docs/reference/modal.parameter#modalparameter)






* * *

# modal.runner

## modal.runner.DeployResult

```
class DeployResult(object)
```

Copy

Dataclass representing the result of deploying an app.

```
def __init__(self, app_id: str, app_page_url: str, app_logs_url: str, warnings: list[str]) -> None
```

Copy

## modal.runner.deploy\_app

```
async def deploy_app(
    app: _App,
    name: Optional[str] = None,
    namespace: Any = api_pb2.DEPLOYMENT_NAMESPACE_WORKSPACE,
    client: Optional[_Client] = None,
    environment_name: Optional[str] = None,
    tag: str = "",
) -> DeployResult:
```

Copy

Deploy an app and export its objects persistently.

Typically, using the command-line tool `modal deploy script>`
should be used, instead of this method.

**Usage:**

```
if __name__ == "__main__":
    deploy_app(app)
```

Copy

Deployment has two primary purposes:

- Persists all of the objects in the app, allowing them to live past the
current app run. For schedules this enables headless “cron”-like
functionality where scheduled functions continue to be invoked after
the client has disconnected.
- Allows for certain kinds of these objects, _deployment objects_, to be
referred to and used by other apps.

## modal.runner.interactive\_shell

```
async def interactive_shell(
    _app: _App, cmds: list[str], environment_name: str = "", pty: bool = True, **kwargs: Any
) -> None:
```

Copy

Run an interactive shell (like `bash`) within the image for this app.

This is useful for online debugging and interactive exploration of the
contents of this image. If `cmd` is optionally provided, it will be run
instead of the default shell inside this image.

**Example**

```
import modal

app = modal.App(image=modal.Image.debian_slim().apt_install("vim"))
```

Copy

You can now run this using

```
modal shell script.py --cmd /bin/bash
```

Copy

When calling programmatically, `kwargs` are passed to `Sandbox.create()`.

[modal.runner](https://modal.com/docs/reference/modal.runner#modalrunner) [modal.runner.DeployResult](https://modal.com/docs/reference/modal.runner#modalrunnerdeployresult) [modal.runner.deploy\_app](https://modal.com/docs/reference/modal.runner#modalrunnerdeploy_app) [modal.runner.interactive\_shell](https://modal.com/docs/reference/modal.runner#modalrunnerinteractive_shell)






* * *

# modal.web\_endpoint

```
def web_endpoint(
    _warn_parentheses_missing=None,
    *,
    method: str = "GET",  # REST method for the created endpoint.
    label: Optional[str] = None,  # Label for created endpoint. Final subdomain will be --.modal.run.
    docs: bool = False,  # Whether to enable interactive documentation for this endpoint at /docs.
    custom_domains: Optional[\
        Iterable[str]\
    ] = None,  # Create an endpoint using a custom domain fully-qualified domain name (FQDN).
    requires_proxy_auth: bool = False,  # Require Proxy-Authorization HTTP Headers on requests
    wait_for_response: bool = True,  # DEPRECATED: this must always be True now
) -> Callable[[Callable[P, ReturnType]], _PartialFunction[P, ReturnType, ReturnType]]:
```

Copy

Register a basic web endpoint with this application.

This is the simple way to create a web endpoint on Modal. The function
behaves as a [FastAPI](https://fastapi.tiangolo.com/) handler and should
return a response object to the caller.

Endpoints created with `@app.web_endpoint` are meant to be simple, single
request handlers and automatically have
[CORS](https://developer.mozilla.org/en-US/docs/Web/HTTP/CORS) enabled.
For more flexibility, use `@app.asgi_app`.

To learn how to use Modal with popular web frameworks, see the
[guide on web endpoints](https://modal.com/docs/guide/webhooks).

[modal.web\_endpoint](https://modal.com/docs/reference/modal.web_endpoint#modalweb_endpoint)






* * *

# modal.web\_server

```
def web_server(
    port: int,
    *,
    startup_timeout: float = 5.0,  # Maximum number of seconds to wait for the web server to start.
    label: Optional[str] = None,  # Label for created endpoint. Final subdomain will be --.modal.run.
    custom_domains: Optional[Iterable[str]] = None,  # Deploy this endpoint on a custom domain.
    requires_proxy_auth: bool = False,  # Require Proxy-Authorization HTTP Headers on requests
) -> Callable[[Callable[..., Any]], _PartialFunction]:
```

Copy

Decorator that registers an HTTP web server inside the container.

This is similar to `@asgi_app` and `@wsgi_app`, but it allows you to expose a full HTTP server
listening on a container port. This is useful for servers written in other languages like Rust,
as well as integrating with non-ASGI frameworks like aiohttp and Tornado.

**Usage:**

```
import subprocess

@app.function()
@modal.web_server(8000)
def my_file_server():
    subprocess.Popen("python -m http.server -d / 8000", shell=True)
```

Copy

The above example starts a simple file server, displaying the contents of the root directory.
Here, requests to the web endpoint will go to external port 8000 on the container. The
`http.server` module is included with Python, but you could run anything here.

Internally, the web server is transparently converted into a web endpoint by Modal, so it has
the same serverless autoscaling behavior as other web endpoints.

For more info, see the [guide on web endpoints](https://modal.com/docs/guide/webhooks).

[modal.web\_server](https://modal.com/docs/reference/modal.web_server#modalweb_server)






* * *

# modal.wsgi\_app

```
def wsgi_app(
    _warn_parentheses_missing=None,
    *,
    label: Optional[str] = None,  # Label for created endpoint. Final subdomain will be --.modal.run.
    custom_domains: Optional[Iterable[str]] = None,  # Deploy this endpoint on a custom domain.
    requires_proxy_auth: bool = False,  # Require Proxy-Authorization HTTP Headers on requests
    wait_for_response: bool = True,  # DEPRECATED: this must always be True now
) -> Callable[[Callable[..., Any]], _PartialFunction]:
```

Copy

Decorator for registering a WSGI app with a Modal function.

Web Server Gateway Interface (WSGI) is a standard for synchronous Python web apps.
It has been [succeeded by the ASGI interface](https://asgi.readthedocs.io/en/latest/introduction.html#wsgi-compatibility)
which is compatible with ASGI and supports additional functionality such as web sockets.
Modal supports ASGI via [`asgi_app`](https://modal.com/docs/reference/modal.asgi_app).

**Usage:**

```
from typing import Callable

@app.function()
@modal.wsgi_app()
def create_wsgi() -> Callable:
    ...
```

Copy

To learn how to use this decorator with popular web frameworks, see the
[guide on web endpoints](https://modal.com/docs/guide/webhooks).

[modal.wsgi\_app](https://modal.com/docs/reference/modal.wsgi_app#modalwsgi_app)






* * *

# modal.exception

## modal.exception.AuthError

```
class AuthError(modal.exception.Error)
```

Copy

Raised when a client has missing or invalid authentication.

## modal.exception.ClientClosed

```
class ClientClosed(modal.exception.Error)
```

Copy

## modal.exception.ConnectionError

```
class ConnectionError(modal.exception.Error)
```

Copy

Raised when an issue occurs while connecting to the Modal servers.

## modal.exception.DeprecationError

```
class DeprecationError(UserWarning)
```

Copy

UserWarning category emitted when a deprecated Modal feature or API is used.

## modal.exception.DeserializationError

```
class DeserializationError(modal.exception.Error)
```

Copy

Raised to provide more context when an error is encountered during deserialization.

## modal.exception.ExecutionError

```
class ExecutionError(modal.exception.Error)
```

Copy

Raised when something unexpected happened during runtime.

## modal.exception.FilesystemExecutionError

```
class FilesystemExecutionError(modal.exception.Error)
```

Copy

Raised when an unknown error is thrown during a container filesystem operation.

## modal.exception.FunctionTimeoutError

```
class FunctionTimeoutError(modal.exception.TimeoutError)
```

Copy

Raised when a Function exceeds its execution duration limit and times out.

## modal.exception.InputCancellation

```
class InputCancellation(BaseException)
```

Copy

Raised when the current input is cancelled by the task

Intentionally a BaseException instead of an Exception, so it won’t get
caught by unspecified user exception clauses that might be used for retries and
other control flow.

## modal.exception.InteractiveTimeoutError

```
class InteractiveTimeoutError(modal.exception.TimeoutError)
```

Copy

Raised when interactive frontends time out while trying to connect to a container.

## modal.exception.InternalFailure

```
class InternalFailure(modal.exception.Error)
```

Copy

Retriable internal error.

## modal.exception.InvalidError

```
class InvalidError(modal.exception.Error)
```

Copy

Raised when user does something invalid.

## modal.exception.ModuleNotMountable

```
class ModuleNotMountable(Exception)
```

Copy

## modal.exception.MountUploadTimeoutError

```
class MountUploadTimeoutError(modal.exception.TimeoutError)
```

Copy

Raised when a Mount upload times out.

## modal.exception.NotFoundError

```
class NotFoundError(modal.exception.Error)
```

Copy

Raised when a requested resource was not found.

## modal.exception.OutputExpiredError

```
class OutputExpiredError(modal.exception.TimeoutError)
```

Copy

Raised when the Output exceeds expiration and times out.

## modal.exception.PendingDeprecationError

```
class PendingDeprecationError(UserWarning)
```

Copy

Soon to be deprecated feature. Only used intermittently because of multi-repo concerns.

## modal.exception.RemoteError

```
class RemoteError(modal.exception.Error)
```

Copy

Raised when an error occurs on the Modal server.

## modal.exception.RequestSizeError

```
class RequestSizeError(modal.exception.Error)
```

Copy

Raised when an operation produces a gRPC request that is rejected by the server for being too large.

## modal.exception.SandboxTerminatedError

```
class SandboxTerminatedError(modal.exception.Error)
```

Copy

Raised when a Sandbox is terminated for an internal reason.

## modal.exception.SandboxTimeoutError

```
class SandboxTimeoutError(modal.exception.TimeoutError)
```

Copy

Raised when a Sandbox exceeds its execution duration limit and times out.

## modal.exception.SerializationError

```
class SerializationError(modal.exception.Error)
```

Copy

Raised to provide more context when an error is encountered during serialization.

## modal.exception.ServerWarning

```
class ServerWarning(UserWarning)
```

Copy

Warning originating from the Modal server and re-issued in client code.

## modal.exception.TimeoutError

```
class TimeoutError(modal.exception.Error)
```

Copy

Base class for Modal timeouts.

## modal.exception.VersionError

```
class VersionError(modal.exception.Error)
```

Copy

Raised when the current client version of Modal is unsupported.

## modal.exception.VolumeUploadTimeoutError

```
class VolumeUploadTimeoutError(modal.exception.TimeoutError)
```

Copy

Raised when a Volume upload times out.

## modal.exception.simulate\_preemption

```
def simulate_preemption(wait_seconds: int, jitter_seconds: int = 0):
```

Copy

Utility for simulating a preemption interrupt after `wait_seconds` seconds.
The first interrupt is the SIGINT signal. After 30 seconds, a second
interrupt will trigger.

This second interrupt simulates SIGKILL, and should not be caught.
Optionally add between zero and `jitter_seconds` seconds of additional waiting before first interrupt.

**Usage:**

```
import time
from modal.exception import simulate_preemption

simulate_preemption(3)

try:
    time.sleep(4)
except KeyboardInterrupt:
    print("got preempted") # Handle interrupt
    raise
```

Copy

See [https://modal.com/docs/guide/preemption](https://modal.com/docs/guide/preemption) for more details on preemption
handling.

[modal.exception](https://modal.com/docs/reference/modal.exception#modalexception) [modal.exception.AuthError](https://modal.com/docs/reference/modal.exception#modalexceptionautherror) [modal.exception.ClientClosed](https://modal.com/docs/reference/modal.exception#modalexceptionclientclosed) [modal.exception.ConnectionError](https://modal.com/docs/reference/modal.exception#modalexceptionconnectionerror) [modal.exception.DeprecationError](https://modal.com/docs/reference/modal.exception#modalexceptiondeprecationerror) [modal.exception.DeserializationError](https://modal.com/docs/reference/modal.exception#modalexceptiondeserializationerror) [modal.exception.ExecutionError](https://modal.com/docs/reference/modal.exception#modalexceptionexecutionerror) [modal.exception.FilesystemExecutionError](https://modal.com/docs/reference/modal.exception#modalexceptionfilesystemexecutionerror) [modal.exception.FunctionTimeoutError](https://modal.com/docs/reference/modal.exception#modalexceptionfunctiontimeouterror) [modal.exception.InputCancellation](https://modal.com/docs/reference/modal.exception#modalexceptioninputcancellation) [modal.exception.InteractiveTimeoutError](https://modal.com/docs/reference/modal.exception#modalexceptioninteractivetimeouterror) [modal.exception.InternalFailure](https://modal.com/docs/reference/modal.exception#modalexceptioninternalfailure) [modal.exception.InvalidError](https://modal.com/docs/reference/modal.exception#modalexceptioninvaliderror) [modal.exception.ModuleNotMountable](https://modal.com/docs/reference/modal.exception#modalexceptionmodulenotmountable) [modal.exception.MountUploadTimeoutError](https://modal.com/docs/reference/modal.exception#modalexceptionmountuploadtimeouterror) [modal.exception.NotFoundError](https://modal.com/docs/reference/modal.exception#modalexceptionnotfounderror) [modal.exception.OutputExpiredError](https://modal.com/docs/reference/modal.exception#modalexceptionoutputexpirederror) [modal.exception.PendingDeprecationError](https://modal.com/docs/reference/modal.exception#modalexceptionpendingdeprecationerror) [modal.exception.RemoteError](https://modal.com/docs/reference/modal.exception#modalexceptionremoteerror) [modal.exception.RequestSizeError](https://modal.com/docs/reference/modal.exception#modalexceptionrequestsizeerror) [modal.exception.SandboxTerminatedError](https://modal.com/docs/reference/modal.exception#modalexceptionsandboxterminatederror) [modal.exception.SandboxTimeoutError](https://modal.com/docs/reference/modal.exception#modalexceptionsandboxtimeouterror) [modal.exception.SerializationError](https://modal.com/docs/reference/modal.exception#modalexceptionserializationerror) [modal.exception.ServerWarning](https://modal.com/docs/reference/modal.exception#modalexceptionserverwarning) [modal.exception.TimeoutError](https://modal.com/docs/reference/modal.exception#modalexceptiontimeouterror) [modal.exception.VersionError](https://modal.com/docs/reference/modal.exception#modalexceptionversionerror) [modal.exception.VolumeUploadTimeoutError](https://modal.com/docs/reference/modal.exception#modalexceptionvolumeuploadtimeouterror) [modal.exception.simulate\_preemption](https://modal.com/docs/reference/modal.exception#modalexceptionsimulate_preemption)






* * *

# modal.config

Modal intentionally keeps configurability to a minimum.

The main configuration options are the API tokens: the token id and the token secret.
These can be configured in two ways:

1. By running the `modal token set` command.
This writes the tokens to `.modal.toml` file in your home directory.
2. By setting the environment variables `MODAL_TOKEN_ID` and `MODAL_TOKEN_SECRET`.
This takes precedence over the previous method.

## .modal.toml

The `.modal.toml` file is generally stored in your home directory.
It should look like this::

```
[default]
token_id = "ak-12345..."
token_secret = "as-12345..."
```

Copy

You can create this file manually, or you can run the `modal token set ...`
command (see below).

## Setting tokens using the CLI

You can set a token by running the command::

```
modal token set \
  --token-id  \
  --token-secret 
```

Copy

This will write the token id and secret to `.modal.toml`.

If the token id or secret is provided as the string `-` (a single dash),
then it will be read in a secret way from stdin instead.

## Other configuration options

Other possible configuration options are:

- `loglevel` (in the .toml file) / `MODAL_LOGLEVEL` (as an env var).
Defaults to `WARNING`. Set this to `DEBUG` to see internal messages.
- `logs_timeout` (in the .toml file) / `MODAL_LOGS_TIMEOUT` (as an env var).
Defaults to 10.
Number of seconds to wait for logs to drain when closing the session,
before giving up.
- `automount` (in the .toml file) / `MODAL_AUTOMOUNT` (as an env var).
Defaults to True.
By default, Modal automatically mounts modules imported in the current scope, that
are deemed to be “local”. This can be turned off by setting this to False.
- `force_build` (in the .toml file) / `MODAL_FORCE_BUILD` (as an env var).
Defaults to False.
When set, ignores the Image cache and builds all Image layers. Note that this
will break the cache for all images based on the rebuilt layers, so other images
may rebuild on subsequent runs / deploys even if the config is reverted.
- `traceback` (in the .toml file) / `MODAL_TRACEBACK` (as an env var).
Defaults to False. Enables printing full tracebacks on unexpected CLI
errors, which can be useful for debugging client issues.

## Meta-configuration

Some “meta-options” are set using environment variables only:

- `MODAL_CONFIG_PATH` lets you override the location of the .toml file,
by default `~/.modal.toml`.
- `MODAL_PROFILE` lets you use multiple sections in the .toml file
and switch between them. It defaults to “default”.

## modal.config.Config

```
class Config(object)
```

Copy

Singleton that holds configuration used by Modal internally.

```
def __init__(self):
```

Copy

### get

```
def get(self, key, profile=None, use_env=True):
```

Copy

Looks up a configuration value.

Will check (in decreasing order of priority):

1. Any environment variable of the form MODAL\_FOO\_BAR (when use\_env is True)
2. Settings in the user’s .toml configuration file
3. The default value of the setting

### override\_locally

```
def override_locally(self, key: str, value: str):
    # Override setting in this process by overriding environment variable for the setting
    #
    # Does NOT write back to settings file etc.
```

Copy

### to\_dict

```
def to_dict(self):
```

Copy

## modal.config.config\_profiles

```
def config_profiles():
```

Copy

List the available modal profiles in the .modal.toml file.

## modal.config.config\_set\_active\_profile

```
def config_set_active_profile(env: str) -> None:
```

Copy

Set the user’s active modal profile by writing it to the `.modal.toml` file.

[modal.config](https://modal.com/docs/reference/modal.config#modalconfig) [.modal.toml](https://modal.com/docs/reference/modal.config#modaltoml) [Setting tokens using the CLI](https://modal.com/docs/reference/modal.config#setting-tokens-using-the-cli) [Other configuration options](https://modal.com/docs/reference/modal.config#other-configuration-options) [Meta-configuration](https://modal.com/docs/reference/modal.config#meta-configuration) [modal.config.Config](https://modal.com/docs/reference/modal.config#modalconfigconfig) [get](https://modal.com/docs/reference/modal.config#get) [override\_locally](https://modal.com/docs/reference/modal.config#override_locally) [to\_dict](https://modal.com/docs/reference/modal.config#to_dict) [modal.config.config\_profiles](https://modal.com/docs/reference/modal.config#modalconfigconfig_profiles) [modal.config.config\_set\_active\_profile](https://modal.com/docs/reference/modal.config#modalconfigconfig_set_active_profile)

