# DLL telemetry adapter

`satan1c-dev.patch` targets Satan1c/XXMI-Libs-Package at
`e930c66752c2561fa7cf7bce9700b17a462bcc64`. Apply it in a disposable source
checkout and build the DLL with the project's usual Windows toolchain.
The patch is covered by the [GPLv3](LICENSE.GPL.txt), matching the DLL source.

```sh
git apply --check /absolute/path/to/xxmi-runtime-mcp/adapters/satan1c-dev.patch
git apply /absolute/path/to/xxmi-runtime-mcp/adapters/satan1c-dev.patch
```

The patch uses the existing info log and samples fields where the overlay
already reads them. It emits changed values under the `XXMI_MCP/1` prefix.
Selection records carry lowercase hexadecimal values and the all-ones sentinel
for empty slots. Performance records enclose the profiling overlay text between
`performance begin` and `performance end` lines. Published values are the
last readings observed while those overlays were drawn.

When updating the DLL, check `Overlay.cpp` for the current selection and
profiling fields, `input.cpp` and `Hunting.cpp` for registration log changes,
and `HackerDXGI.cpp` and `Hunting.cpp` for dump completion. Update the
patch and its base revision together. Retain v1 records if their meaning
is preserved. For incompatible changes, add a protocol version and update
the companion parser and fixtures before deploying both together.
