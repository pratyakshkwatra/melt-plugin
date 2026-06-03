from setuptools import setup

setup(
    name="OctoPrint-Melt",
    version="0.1.0",
    description="An OctoPrint server extension that provides a custom dashboard UI for live printer stats, manages local data storage, and aggregates real-time telemetry. Features a high throughput WebSocket API built to power the Melt cross platform app.",
    author="Pratyaksh Kwatra",
    url="https://www.github.com/pratyakshkwatra",
    packages=["octoprint_melt"],
    include_package_data=True,
    zip_safe=False,
    entry_points={
        "octoprint.plugin": [
            "melt = octoprint_melt:MeltPlugin"
        ]
    },
)
