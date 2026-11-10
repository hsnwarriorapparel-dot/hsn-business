# Upgrading Hermes and the browser stack

## THE PLUGIN NEEDED A NEWER HERMES THAN WE RAN

`sagarmainkar/hermes-genui` declares `requires_hermes: ">=0.22.5"`. We were
on 0.21.6, so `hermes plugins install` refused with:

```
Error: Plugin 'hermes-genui' requires hermes >=0.22.5, running 0.21.6
```

**Read the plugin's `plugin.yaml` before installing.** The README says
the same thing, but the manifest is the machine-readable source.

## A GATEWAY RESTART KILLS THE BROWSER AND THE X SERVER

The whole browser stack dies together, and nothing restarts it:

- the Xvnc display (`:21`) - `xdpyinfo -display :21` fails
- the Chromium work browser (CDP on 9222) - `ss -ltnp` shows nothing

**A script blocked on a dead CDP endpoint hangs forever.** `screen_buyers.py`
was found in `hrtimer_nanosleep` with flat CPU and no children - it was
retrying a browser that no longer existed, and it held the whole
go4WorldBusiness funnel hostage for 30+ minutes.

**The symptom to recognise:** a python process in `hrtimer_nanosleep`,
flat utime, and NO child processes. It is not slow, it is stuck.

**Restart the stack in this order:**

```bash
# 1. the display
DISPLAY=:21 nohup Xvnc :21 -geometry 1920x1080 -depth 24 \
  -rfbport 5922 -localhost no -rfbauth /home/ubuntu/.vncpassfile &
# 2. the window manager
DISPLAY=:21 nohup xfwm4 --display=:21 --replace --compositor=off &
# 3. the browser (launch_work_browser.sh picks a LIVE display itself)
bash /home/ubuntu/launch_work_browser.sh
```

`launch_work_browser.sh` refuses to start when no display is live - it
prints `NO LIVE VIRTUAL DISPLAY`. That is the tell that the X server is
the missing piece, not the browser.

**Verify the whole stack afterwards, not just the browser:**

```bash
curl -s http://127.0.0.1:9222/json/version     # CDP alive
python3 wa_deep_check.py                       # WhatsApp still logged in
```

## `hermes update` DEADLOCKS ON THE TURN THAT RUNS IT

The updater drains the gateway before swapping the code, and it counts
the running CHAT TURN as a work unit. So the turn that launched
`hermes update` is the thing the update is waiting for.

The updater has a fire-and-forget path for the case where the gateway is
an ANCESTOR of the updater - but a chat turn runs `hermes update` as a
CHILD of the gateway, so it takes the graceful drain path and waits for
the turn to end.

**The way out:** let the turn END. The drain has a force-restart cap
(`agent.restart_after_turn_timeout`, 1800s by default); when it fires the
gateway restarts and the update completes. The session is restored
afterwards.

**Never kill a running business job to clear the drain unless it is
genuinely stuck.** A slow `screen_buyers.py` is normal - it fetches one
profile at a time. Check for progress before killing it:

```bash
grep -E '^\s+[0-9]+/[0-9]+ \| ours=' <log> | tail -3   # is it advancing?
```

**A hung job and a slow job look the same from the outside.** The
difference: flat utime across two samples plus no child processes means
hung; a changing progress counter means slow.
