<!-- .. image:: https://img.shields.io/pypi/v/mode-streaming.svg
    :target: https://pypi.python.org/pypi/mode-streaming/

.. image:: https://img.shields.io/pypi/pyversions/mode-streaming.svg
    :target: https://pypi.org/project/mode-streaming/

.. image:: https://img.shields.io/pypi/dm/mode-streaming
   :target: https://pypi.python.org/pypi/mode-streaming/

:Web: https://faust-streaming.github.io/mode/
:Download: http://pypi.org/project/mode-streaming
:Source: http://github.com/faust-streaming/mode
:Keywords: async, service, framework, actors, bootsteps, graph -->

Mode is a very minimal Python library built-on top of AsyncIO that makes
it much easier to use.

In Mode your program is built out of services that you can start, stop,
restart and supervise.

A service is just a class:

```python
class PageViewCache(Service):
    redis: Redis = None

    async def on_start(self) -> None:
        self.redis = connect_to_redis()

    async def update(self, url: str, n: int = 1) -> int:
        return await self.redis.incr(url, n)

    async def get(self, url: str) -> int:
        return await self.redis.get(url)
```

Services are started, stopped and restarted and have
callbacks for those actions.

It can start another service:

```python
class App(Service):
    page_view_cache: PageViewCache = None

    async def on_start(self) -> None:
        await self.add_runtime_dependency(self.page_view_cache)

    @cached_property
    def page_view_cache(self) -> PageViewCache:
        return PageViewCache()
```

It can include background tasks:

```python
class PageViewCache(Service):

    @Service.timer(1.0)
    async def _update_cache(self) -> None:
        self.data = await cache.get('key')
```

Services that depends on other services actually form a graph
that you can visualize.

### Worker

Mode optionally provides a worker that you can use to start the program,
with support for logging, blocking detection, remote debugging and more.

To start a worker add this to your program:

```python
if __name__ == '__main__':
    from mode import Worker
    Worker(Service(), loglevel="info").execute_from_commandline()
```

Then execute your program to start the worker:

```sh
$ python examples/tutorial.py
[2018-03-27 15:47:12,159: INFO]: [^Worker]: Starting...
[2018-03-27 15:47:12,160: INFO]: [^-AppService]: Starting...
[2018-03-27 15:47:12,160: INFO]: [^--Websockets]: Starting...
STARTING WEBSOCKET SERVER
[2018-03-27 15:47:12,161: INFO]: [^--UserCache]: Starting...
[2018-03-27 15:47:12,161: INFO]: [^--Webserver]: Starting...
[2018-03-27 15:47:12,164: INFO]: [^--Webserver]: Serving on port 8000
REMOVING EXPIRED USERS
REMOVING EXPIRED USERS
```

To stop it hit `Control-c`:

```sh
[2018-03-27 15:55:08,084: INFO]: [^Worker]: Stopping on signal received...
[2018-03-27 15:55:08,084: INFO]: [^Worker]: Stopping...
[2018-03-27 15:55:08,084: INFO]: [^-AppService]: Stopping...
[2018-03-27 15:55:08,084: INFO]: [^--UserCache]: Stopping...
REMOVING EXPIRED USERS
[2018-03-27 15:55:08,085: INFO]: [^Worker]: Gathering service tasks...
[2018-03-27 15:55:08,085: INFO]: [^--UserCache]: -Stopped!
[2018-03-27 15:55:08,085: INFO]: [^--Webserver]: Stopping...
[2018-03-27 15:55:08,085: INFO]: [^Worker]: Gathering all futures...
[2018-03-27 15:55:08,085: INFO]: [^--Webserver]: Closing server
[2018-03-27 15:55:08,086: INFO]: [^--Webserver]: Waiting for server to close handle
[2018-03-27 15:55:08,086: INFO]: [^--Webserver]: Shutting down web application
[2018-03-27 15:55:08,086: INFO]: [^--Webserver]: Waiting for handler to shut down
[2018-03-27 15:55:08,086: INFO]: [^--Webserver]: Cleanup
[2018-03-27 15:55:08,086: INFO]: [^--Webserver]: -Stopped!
[2018-03-27 15:55:08,086: INFO]: [^--Websockets]: Stopping...
[2018-03-27 15:55:08,086: INFO]: [^--Websockets]: -Stopped!
[2018-03-27 15:55:08,087: INFO]: [^-AppService]: -Stopped!
[2018-03-27 15:55:08,087: INFO]: [^Worker]: -Stopped!
```

### Beacons

The `beacon` object that we pass to services keeps track of the services
in a graph.

They are not strictly required, but can be used to visualize a running
system, for example we can render it as a pretty graph.

This requires you to have the `pydot` library and GraphViz
installed:

```sh
$ pip install pydot
```

Let's change the app service class to dump the graph to an image
at startup:


```python
class AppService(Service):

    async def on_start(self) -> None:
        print('APP STARTING')
        import pydot
        import io
        o = io.StringIO()
        beacon = self.app.beacon.root or self.app.beacon
        beacon.as_graph().to_dot(o)
        graph, = pydot.graph_from_dot_data(o.getvalue())
        print('WRITING GRAPH TO image.png')
        with open('image.png', 'wb') as fh:
            fh.write(graph.create_png())
```
