# TV Taste Notes

Explore 89,594 TV shows, build a watched list, and find recommendations with adjustable similarities and multidimensional radar charts.

[![Deploy to Rigbox](https://rigbox.dev/deploy.svg)](https://rigbox.dev/deploy?repo=jona62%2Ftv-show-research&ref=main&path=rig.yaml)

[Live demo](https://tv-taste-jlvf21do.rigbox.dev/) · [Research](output/research-report.md) · [Development & dataset updates](site/README.md)

Run locally with Python 3.10+ (no runtime dependencies):

```sh
python3 site/server.py
```

Open <http://localhost:8080>. The prebuilt model is included; watched lists stay in your browser. The deploy button forks the public repository and configures a Rigbox workspace.

Data: [TVmaze](https://www.tvmaze.com/) ([CC BY-SA 4.0](https://creativecommons.org/licenses/by-sa/4.0/)). Theme signals are inferred from summaries; similarity is not a guarantee of enjoyment.
