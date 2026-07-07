# whisper.cpp compilé pour Blackwell (sm_120, RTX 5080) — les images officielles
# ggml-org/whisper.cpp:main-cuda n'embarquent que les archs 750→900 et retombent
# silencieusement sur le CPU (~6-10 s par phrase, voir docs/impasses.md 2026-07-07).
# Même famille de remède que l'override torch cu128 du Voice Forge (ADR 0002).
ARG CUDA_VERSION=12.8.1

FROM nvidia/cuda:${CUDA_VERSION}-devel-ubuntu24.04 AS build
RUN apt-get update && apt-get install -y --no-install-recommends \
      git cmake build-essential ca-certificates \
    && rm -rf /var/lib/apt/lists/*
# v1.9.1 = dernière release au 2026-07-07
RUN git clone --depth 1 --branch v1.9.1 https://github.com/ggml-org/whisper.cpp /src
WORKDIR /src
RUN cmake -B build \
      -DGGML_CUDA=1 \
      -DCMAKE_CUDA_ARCHITECTURES=120 \
      -DBUILD_SHARED_LIBS=OFF \
      -DCMAKE_BUILD_TYPE=Release \
    && cmake --build build -j 4 --target whisper-server
    # -j 4 impératif : -j sans limite lance ~16 nvcc × ~2 Go sur la VM WSL de
    # 30 Go déjà occupée par la stack → OOM, vmmem figé, « WSL server » mort,
    # PC à redémarrer (vécu 3× le 2026-07-07, voir docs/impasses.md).

FROM nvidia/cuda:${CUDA_VERSION}-runtime-ubuntu24.04
RUN apt-get update && apt-get install -y --no-install-recommends \
      ffmpeg curl \
    && rm -rf /var/lib/apt/lists/*
COPY --from=build /src/build/bin/whisper-server /usr/local/bin/whisper-server
ENTRYPOINT ["whisper-server"]
