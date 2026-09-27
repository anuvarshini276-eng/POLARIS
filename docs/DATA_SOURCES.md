# Data provenance

All research documents, datasets, expedition programmes and educational charts are explicitly synthetic demonstrations. Station names and approximate coordinates provide geographic context, not operational station metadata.

The offline map uses the `world-atlas` package's `land-110m.json`, derived from Natural Earth 1:110m land geometry. Natural Earth data is public domain. The preparation script converts TopoJSON into GeoJSON; no map service, API key or runtime network request is required. Source package: https://github.com/topojson/world-atlas . Natural Earth: https://www.naturalearthdata.com/about/terms-of-use/ . The bundled geometry is low resolution and is unsuitable for navigation or precise scientific mapping.

Media charts are generated from invented monthly temperatures by scripts/seed_media.py. Their captions state that they are not observations. User-uploaded sources retain their own rights and provenance.
