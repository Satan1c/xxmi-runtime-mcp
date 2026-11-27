# DLL telemetry adapter

`satan1c-dev.patch` targets Satan1c/XXMI-Libs-Package at
the commit recorded in [base-revision.txt](base-revision.txt). Apply it in a disposable source
checkout and build the DLL with the project's usual Windows toolchain.
The patch is covered by the [GPLv3](LICENSE.GPL.txt), matching the DLL source.

```sh
git apply --check /absolute/path/to/xxmi-runtime-mcp/adapters/satan1c-dev.patch
git apply /absolute/path/to/xxmi-runtime-mcp/adapters/satan1c-dev.patch
```

The CI workflow builds the patched Windows x64 DLL and publishes it as the
`xxmi-patched-windows-x64` artifact.

The patch uses the existing info log and samples fields where the overlay
already reads them. It emits changed values under the `XXMI_MCP/1` prefix.
Selection records carry lowercase hexadecimal values and the all-ones sentinel
for empty slots. The hunting callbacks emit `hunt <action> <hash|none>`
after each next or previous shader or buffer action, including steps that
select the same hash. Performance records enclose the profiling overlay text between
`performance begin` and `performance end` lines. Published values are the
last readings observed while those overlays were drawn.

When updating the DLL, check `Overlay.cpp` for the current selection and
profiling fields, `input.cpp` and `Hunting.cpp` for registration log changes,
and `HackerDXGI.cpp` and `Hunting.cpp` for dump completion. Update the
patch and its base revision together. Retain v1 records if their meaning
is preserved. For incompatible changes, add a protocol version and update
the companion parser and fixtures before deploying both together.
