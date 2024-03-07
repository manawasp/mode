
# Creating a Service

To define a service, simply subclass and fill in the methods
to do stuff as the service is started/stopped etc.:

```python
class MyService(Service):

    async def on_start(self) -> None:
        print('Im starting now')

    async def on_started(self) -> None:
        print('Im ready')

    async def on_stop(self) -> None:
        print('Im stopping now')
```

To start the service, call ``await service.start()``:

```python
await service.start()
```

Or you can use ``mode.Worker`` (or a subclass of this) to start your
services-based asyncio program from the console:

```python
if __name__ == '__main__':
    import mode
    worker = mode.Worker(
        MyService(),
        loglevel='INFO',
        logfile=None,
        daemon=False,
    )
    worker.execute_from_commandline()
```

## It's a Graph!

Services can start other services, coroutines, and background tasks.

1) Starting other services using ``add_dependency``:

```python
 class MyService(Service):

     def __post_init__(self) -> None:
        self.add_dependency(OtherService(loop=self.loop))
```

1) Start a list of services using ``on_init_dependencies``:

```python
class MyService(Service):

    def on_init_dependencies(self) -> None:
        return [
            ServiceA(loop=self.loop),
            ServiceB(loop=self.loop),
            ServiceC(loop=self.loop),
        ]
```

1) Start a future/coroutine (that will be waited on to complete on stop):

```python
 class MyService(Service):

     async def on_start(self) -> None:
         self.add_future(self.my_coro())

     async def my_coro(self) -> None:
         print('Executing coroutine')
```

1) Start a background task:

```python
class MyService(Service):

    @Service.task
    async def _my_coro(self) -> None:
        print('Executing coroutine')
```


1) Start a background task that keeps running:

```python
class MyService(Service):

    @Service.task
    async def _my_coro(self) -> None:
        while not self.should_stop:
            # NOTE: self.sleep will wait for one second, or
            #       until service stopped/crashed.
            await self.sleep(1.0)
            print('Background thread waking up')
```
