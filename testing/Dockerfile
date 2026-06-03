FROM octoprint/octoprint:latest

# Install dependencies using the correct OctoPrint virtual environment
RUN /usr/local/bin/python -m pip install \
    "https://github.com/jneilliii/OctoPrint-BedLevelVisualizer/archive/master.zip" \
    "https://github.com/paukstelis/OctoPrint-Cancelobject/archive/master.zip" \
    "https://github.com/OllisGit/OctoPrint-SpoolManager/archive/master.zip" \
    "https://github.com/eyal0/OctoPrint-PrintTimeGenius/archive/master.zip"

# Enable Virtual Printer by injecting basic config.yaml
# The octoprint/octoprint image uses /octoprint/octoprint as the base directory.
RUN mkdir -p /octoprint/octoprint && \
    echo 'plugins:\n  virtual_printer:\n    enabled: true\nprinterProfiles:\n  default: _default' > /octoprint/octoprint/config.yaml && \
    chmod -R 777 /octoprint/octoprint

# Pre-create the plugin dev mount directory
RUN mkdir -p /melt-plugin

CMD ["octoprint", "serve", "--host=0.0.0.0", "--port=5000", "--basedir=/octoprint/octoprint"]
