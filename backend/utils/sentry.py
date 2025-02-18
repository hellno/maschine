import os


def setup_sentry():
    import sentry_sdk

    SENTRY_DSN = os.environ.get("SENTRY_DSN")
    if SENTRY_DSN:
        print("Sentry init")
        sentry_sdk.init(
            dsn=SENTRY_DSN,
            # Add data like request headers and IP for users,
            # see https://docs.sentry.io/platforms/python/data-management/data-collected/ for more info
            send_default_pii=True,
            # Set traces_sample_rate to 1.0 to capture 100%
            # of transactions for tracing.
            traces_sample_rate=1.0,
            _experiments={
                # Set continuous_profiling_auto_start to True
                # to automatically start the profiler on when
                # possible.
                "continuous_profiling_auto_start": True,
            },
        )
    else:
        print("Sentry DSN not found, no init")
