# G7 Day 6 real-mode retry evidence manifest

Evidence was copied byte-for-byte from the stopped isolated validation worktree.
Hashes use SHA-256.

| File | Bytes | SHA-256 |
|---|---:|---|
| `day-state.json` | 32469 | `bf448a79df6ad88ec94f4ce0956cc5bc4d95a8d5ebefa32ceb299596f8d5205b` |
| `grant.json` | 1255 | `ea64b2520c54fddf5bf6e6ddd3b24e2956d8525d8e67bb84d22e8b031a908faa` |
| `preflight.json` | 1222 | `f2ee33faef80517a53a39ca6cad276b50bdc85d2214a98aa26530ad50f3e54e3` |
| `prerequisite.json` | 571 | `dd1f9223c17e2c4c97bdc2ca51e76552c4689fda8eeeee39fa9f26bf3eda2889` |
| `run-current.json` | 1325 | `69cf07d3bcfd21f3b65c19b8a94039b2f6309a18b3c1856259c861b0b1e72a1b` |
| `run-history-prefight.json` | 1223 | `230b8a471513fcf4b65d60386ffda9cce92e590763e1436853604c8dbce4dbdf` |
| `service-stderr.log` | 202 | `233d213e5df720a3c32de8bfc7d87d1c63b3079e9dfe86add48323dba31e226a` |
| `service-stdout.log` | 21285 | `1e9327128100831911ff1428cca0d626acafd65cc03c4445ad273ed0ab262c62` |

The access log contains exactly one successful
`POST /api/local-llm/day/go` entry. The current RunRecord and Day state share
run ID `run-dbfa4263c3fd47709057548288a9468d`.
