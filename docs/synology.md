# Running on a Synology NAS with Portainer

The NAS is a good permanent home: it is always on, restarts the container by itself, and
Homebridge can live next to it. These steps assume Portainer is already running on the NAS
(tested against a DS923+, which is x86_64, but any model that runs Docker works).

## 1. Before you start

- **Reserve IP addresses** in your router for the NAS and every WLED board. Inside a container
  `.local` names do not resolve, so `config/shelf.yaml` must use IP addresses for controllers.
- **Pick a port.** The web app listens on 8000 inside the container. If something on the NAS
  already uses 8000, choose another host port (for example 8420) for `SHELF_PORT` below.
- **Create the folders** in File Station, inside the `docker` shared folder:
  `docker/recordshelf/data` and `docker/recordshelf/config`. On the NAS these are
  `/volume1/docker/recordshelf/data` and `/volume1/docker/recordshelf/config` (adjust the
  volume number if yours differs).

## 2. Copy your data over (moving from another machine)

Do this before the first deploy, so the container starts with your shelf instead of an empty
one. The database where you file records must only ever be written by one server, so stop
the old one first.

On the old machine, in the recordShelf checkout:

```bash
# stop `recordshelf serve` first (Ctrl+C), then take consistent copies
mkdir -p ~/Desktop/recordshelf-export
sqlite3 data/recordshelf.sqlite ".backup '$HOME/Desktop/recordshelf-export/recordshelf.sqlite'"
sqlite3 data/discogs-details.sqlite ".backup '$HOME/Desktop/recordshelf-export/discogs-details.sqlite'"
cp config/shelf.yaml ~/Desktop/recordshelf-export/
```

Copy the two `.sqlite` files into `docker/recordshelf/data` and `shelf.yaml` into
`docker/recordshelf/config` (Finder → Go → Connect to Server → `smb://<nas>`, or File Station
upload). If `discogs-details.sqlite` does not exist yet, skip it.

If the stack was already deployed and created empty files, stop the stack first and delete
every `recordshelf.sqlite*` and `discogs-details.sqlite*` file (including `-wal` and `-shm`)
and the example `shelf.yaml` before copying yours in. A leftover `-wal` file next to a copied
database can corrupt it.

## 3. Deploy the stack

Portainer → **Stacks → Add stack**:

- **Name:** `recordshelf`
- **Build method:** Repository
- **Repository URL:** `https://github.com/whoismikesmith/recordShelf`
- **Repository reference:** `refs/heads/v2`
- **Compose path:** `docker-compose.yml`
- **Environment variables:**

  | Name | Value |
  | --- | --- |
  | `DISCOGS_USERNAME` | your Discogs username |
  | `DISCOGS_TOKEN` | your personal access token (optional, but needed for folders and prices) |
  | `SHELF_DATA_PATH` | `/volume1/docker/recordshelf/data` |
  | `SHELF_CONFIG_PATH` | `/volume1/docker/recordshelf/config` |
  | `SHELF_PORT` | `8000` (or the port you picked) |
  | `TZ` | your timezone, e.g. `America/Los_Angeles` |

**Deploy the stack.** Portainer clones the repo and builds the image on the NAS; the first
build takes a few minutes. The token only lives in the stack's environment, never in the repo
or the image.

## 4. Check it

- Open `http://<nas-ip>:8000`. The status strip should show your record count and shelf.
- **Layout → Controllers → Probe** each board, then **Test the lights → Identify**.
- In Portainer the container should turn **healthy** within a minute (the health check calls
  `/api/hooks/state`).

After the move, do not run the old server against the boards any more: two servers sending
frames fight over the LEDs. For development on another machine, set its controllers to
`type: none` and work on a copy of the data.

## 5. Fetch release details

Credits, pressing plants and prices come from **Settings → Fetch details**, or from the
container console (Portainer → Containers → recordshelf → Console):

```bash
uv run --no-sync recordshelf enrich
```

It is resumable and rate limited to Discogs' 60 requests a minute, so it takes a while the
first time. Run one or the other, not both at once.

## 6. Updating

Push to the `v2` branch, then Portainer → Stacks → recordshelf → **Pull and redeploy**. Your
data and config are untouched: they live in the mounted folders, not in the image.

If a redeploy does not pick up the change, Portainer reused the image it built last time.
Remove the `recordshelf-recordshelf` image under **Images** and redeploy to force a rebuild.

## Backups

Include `docker/recordshelf` in Hyper Backup. SQLite files copied while the server is writing
can be inconsistent, so for a guaranteed-clean copy stop the stack briefly, or take a
`.backup` copy as in step 2.

## Homebridge

Point the switches in [homebridge.md](homebridge.md) at `http://<nas-ip>:8000`. That works
whether Homebridge runs in host or bridge network mode.
