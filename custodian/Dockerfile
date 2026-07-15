FROM python:3.14.3-alpine3.23@sha256:581c14606911610c6b61e569714e92a726c1ef2437dd034824f644f6d9df6e9d

ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1 \
    PYTHONPATH=/opt/laos/src

WORKDIR /opt/laos

RUN pip install --no-cache-dir --disable-pip-version-check \
      cryptography==49.0.0 pydantic==2.13.4 rfc8785==0.1.4 \
    && addgroup -g 65532 laos-custodian \
    && adduser -D -H -u 65532 -G laos-custodian laos-custodian

COPY src /opt/laos/src

USER 65532:65532
ENTRYPOINT ["python", "-m", "laos_v8.custody_service"]
