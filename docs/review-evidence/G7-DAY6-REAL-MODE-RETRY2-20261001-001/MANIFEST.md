# G7 Day 6 real-mode retry 2 evidence manifest

Evidence was copied byte-for-byte after the isolated service reached its terminal
state and was then stopped. Hashes use SHA-256.

| File | Bytes | SHA-256 |
|---|---:|---|
| `artifacts/temporal_state.py` | 4634 | `ffa740063ae2e6970785e20fb03c47a5696d35e5c0c6198b39f1ba1cfa750c04` |
| `artifacts/temporal-state.md` | 1054 | `c0333bd531bbeb492eccb6c971324b3302a2464400aeeede4b11338986823509` |
| `artifacts/temporal-state.schema.json` | 1394 | `9aed012025e16fb25ad5bbec9f16af4df9123033a4e7dc43e37b4d4ee9e257ca` |
| `artifacts/test_temporal_state.py` | 3070 | `4764ac4731fd41bf5a8d5bc8b426a046c7c22a54d0662d2c510ad1e36b5c05d9` |
| `day-state.json` | 48274 | `4c3f262f8b5677993030185c9a4ca3a217f6d3a59e2d62bcbfa75579567eb13c` |
| `grant.json` | 1256 | `4172544fdb3a20004b73b8dcd66df4d1305e1e29a3251528d316451a594a347a` |
| `preflight.json` | 1224 | `0973e9b009b6e7dd676afc6ee778f339ed80d276c3cd6f7307441d5d95021aa0` |
| `prerequisite.json` | 572 | `54a13cf0585779e7a664aa889ffcbc493c354ef8822b02ede284f7691ca1cfca` |
| `run-current.json` | 1223 | `cb4e392aa41165606b49873612ffe8c8ba249d2a0d219a8dfeca7be52147eef4` |
| `service-stderr.log` | 202 | `8fa313657714c8ad4c8f7b85a3b473c0e028af7c0d997416998fa98816ef19f2` |
| `service-stdout.log` | 59016 | `8b6bac756b6072796dd9bcaf422bdef53b5c1a512627a7b473f0f78c24ce18c9` |
| `startup.json` | 258 | `676c2eedd786273f7aabeaba734ab383de4de9e9ff55ab3031ad2446059eba0c` |

The service log contains exactly one successful `POST /api/local-llm/day/go`.
`startup.json` records the exact configured and resolved managed SQLite path.
