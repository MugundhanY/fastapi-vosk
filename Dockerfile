Line 11: Adds libasound2-dev to the Dockerfile to resolve ALSA errors during Vosk initialization.

BEFORE:
  RUN pip install -r requirements.txt

AFTER:
  RUN pip install -r requirements.txt && apt-get update && apt-get install -y --no-install-recommends libasound2-dev

---
