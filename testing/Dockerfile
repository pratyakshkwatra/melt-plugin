FROM octoprint/octoprint:latest

# No longer pre-installing 3rd party plugins to avoid setuptools crash
# They can be installed via the OctoPrint UI if needed.

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
