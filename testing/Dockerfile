FROM octoprint/octoprint:latest

# Install dependencies using the correct OctoPrint virtual environment
RUN /usr/local/bin/python -m pip install \
    "https://github.com/jneilliii/OctoPrint-BedLevelVisualizer/archive/master.zip" \
    "https://github.com/paukstelis/OctoPrint-Cancelobject/archive/master.zip" \
    "https://github.com/OllisGit/OctoPrint-SpoolManager/archive/master.zip" \
    "https://github.com/eyal0/OctoPrint-PrintTimeGenius/archive/master.zip"

# Enable Virtual Printer by injecting basic config.yaml
RUN mkdir -p /octoprint && \
    echo 'plugins:\n  virtual_printer:\n    enabled: true\nprinterProfiles:\n  default: _default' > /octoprint/config.yaml && \
    chmod -R 777 /octoprint

# Pre-create the plugin dev mount directory
RUN mkdir -p /melt-plugin
