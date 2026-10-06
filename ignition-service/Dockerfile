# ------------------------------------------------------------
# Ignition Maker Edition
# Base: Official Inductive Automation Ignition image
# ------------------------------------------------------------

ARG IGNITION_VERSION=8.3.9

FROM inductiveautomation/ignition:${IGNITION_VERSION}

LABEL application="Ignition Maker Edition"
LABEL description="Ignition Maker Edition container for Google Cloud"

# Ignition Gateway ports
# 8088 = HTTP
# 8043 = HTTPS
# 8060 = Gateway Network
EXPOSE 8088
EXPOSE 8043
EXPOSE 8060

# Persist this directory outside the container.
VOLUME ["/usr/local/bin/ignition/data"]