FROM octoprint/octoprint:latest

# Install dependencies and required third-party plugins
RUN /usr/local/bin/python -m pip install --upgrade pip && \
    /usr/local/bin/python -m pip install \
    "https://github.com/jneilliii/OctoPrint-BedLevelVisualizer/archive/master.zip" \
    "https://github.com/paukstelis/OctoPrint-Cancelobject/archive/master.zip" \
    "https://github.com/OllisGit/OctoPrint-SpoolManager/archive/master.zip" \
    "https://github.com/eyal0/OctoPrint-PrintTimeGenius/archive/master.zip"

# Enable Virtual Printer by injecting basic config.yaml
# The octoprint/octoprint image uses /octoprint/octoprint as the base directory.
RUN mkdir -p /octoprint/octoprint && \
    echo 'plugins:' > /octoprint/octoprint/config.yaml && \
    echo '  virtual_printer:' >> /octoprint/octoprint/config.yaml && \
    echo '    enabled: true' >> /octoprint/octoprint/config.yaml && \
    echo 'printerProfiles:' >> /octoprint/octoprint/config.yaml && \
    echo '  default: _default' >> /octoprint/octoprint/config.yaml

# Create directory for melt-plugin to be mounted
RUN mkdir -p /melt-plugin

CMD ["octoprint", "serve", "--host=0.0.0.0", "--port=5000", "--basedir=/octoprint/octoprint"]
