FROM octoprint/octoprint:latest

USER root

# Install dependencies using the correct OctoPrint virtual environment
# The octoprint image uses python3.10 located in /usr/local/bin/python but plugins must be installed as root before switching user if we don't have sudo.
RUN /usr/local/bin/python -m pip install \
    "https://github.com/jneilliii/OctoPrint-BedLevelVisualizer/archive/master.zip" \
    "https://github.com/paukstelis/OctoPrint-Cancelobject/archive/master.zip" \
    "https://github.com/OllisGit/OctoPrint-SpoolManager/archive/master.zip" \
    "https://github.com/eyal0/OctoPrint-PrintTimeGenius/archive/master.zip"

# Inject virtual printer config
RUN mkdir -p /octoprint && \
    echo 'plugins:\n  virtual_printer:\n    enabled: true\nprinterProfiles:\n  default: _default' > /octoprint/config.yaml && \
    chown -R octoprint:octoprint /octoprint

USER octoprint

CMD ["octoprint", "serve", "--host=0.0.0.0", "--port=5000", "--basedir=/octoprint"]
