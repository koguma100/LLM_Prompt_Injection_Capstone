# Deploying to Oracle Cloud

The web app runs on a free Oracle Cloud VM, in three containers:

    internet ──HTTPS──▶ caddy (ports 80/443, site password) ──▶ web (Flask) ──▶ llm (Ollama, phi3:mini)

Only Caddy is reachable from the internet. It handles HTTPS and asks every visitor for the site password; the web app and Ollama are reachable only from inside Docker's network.

## 1. Create the account

1. Sign up at [oracle.com/cloud/free](https://www.oracle.com/cloud/free/). It asks for a credit card to verify your identity; Always Free resources aren't charged.
2. Choose your **home region** carefully: it can't be changed, and free ARM VMs can only be created there.
3. Optional but recommended: in **Billing & Cost Management → Budgets**, create a budget of $1 with an email alert, so you hear right away if anything starts costing money.

## 2. Create the VM

In the console, go to **Compute → Instances → Create instance**:

- **Image:** Canonical Ubuntu 24.04
- **Shape:** Ampere, `VM.Standard.A1.Flex`, with **2 OCPUs and 12 GB of memory** (the whole free allowance). The shape defaults to 1 OCPU and 6 GB; drag the sliders up. 1 OCPU and 6 GB also works (the containers use about 4 GB), but each request takes about twice as long.
- **Networking:** create a new virtual cloud network with a public subnet, and check **Assign a public IPv4 address**
- **SSH keys:** upload your public key (`~/.ssh/id_ed25519.pub`; create one with `ssh-keygen -t ed25519` if you don't have one)
- **Boot volume:** the default (about 50 GB) is enough

"Out of host capacity" means the free ARM machines in your region are full for now. Try another availability domain, or try again later. Upgrading the account to Pay As You Go usually avoids it; you're still only charged for usage beyond the free limits.

## 3. Open ports 80 and 443

After the VM is created, go to **Networking → Virtual cloud networks** and select your network (check the compartment filter if it isn't listed). On its **Security** tab (in older layouts, **Resources → Security Lists**), open the **Default Security List**, then its **Security rules** tab, and select **Add Ingress Rules**. Add two rules: source CIDR `0.0.0.0/0`, protocol TCP, destination port `80`, and the same for port `443`; leave the source port blank. The existing rule for port 22 (SSH) stays. Port 80 is needed for Let's Encrypt to issue the certificate; Caddy redirects it to HTTPS. Don't open any other ports.

## 4. Install Docker and get the code

    ssh ubuntu@<public IP>
    curl -fsSL https://get.docker.com | sudo sh
    sudo usermod -aG docker ubuntu
    exit

Log back in, then clone the repository:

    ssh ubuntu@<public IP>
    git clone <repository URL>

A private repository needs a [deploy key](https://docs.github.com/en/authentication/connecting-to-github-with-ssh/managing-deploy-keys) or access token on the VM.

The trained BoW models aren't committed, so copy them from your computer (run this locally, from the repository root):

    scp code/models/*.pkl ubuntu@<public IP>:~/LLM_Prompt_Injection_Capstone/code/models/

## 5. Configure and start

On the VM, in `deploy/`:

    cp .env.example .env
    docker run --rm caddy:2.10.2 caddy hash-password --plaintext 'your-password'
    nano .env

In `.env`, set:

- `SITE_ADDRESS`: the public IP with dashes plus `.sslip.io`, e.g. `129-146-12-34.sslip.io`. [sslip.io](https://sslip.io) points that name at the IP, so you don't need to buy a domain.
- `SITE_USER`: the username visitors enter.
- `SITE_PASSWORD_HASH`: the hash printed by `hash-password`, inside single quotes.

Then start everything:

    docker compose up -d --build

The first build takes a while (it downloads PyTorch and the 2 GB model). Open `https://<SITE_ADDRESS>` and log in with the username and password. If the page doesn't load, Oracle's Ubuntu image may be blocking the ports on the VM itself; allow them with:

    sudo iptables -I INPUT 6 -p tcp -m multiport --dports 80,443 -j ACCEPT
    sudo netfilter-persistent save

## 6. Check the deployment

Run the smoke test, from `deploy/` on the VM or on your own computer (it only needs Python 3, no packages):

    python3 smoke_test.py https://<SITE_ADDRESS> --user <SITE_USER>

It asks for the site password (or reads `SMOKE_PASSWORD`), then checks that each page loads, that the forms show their
errors, that a draft saves and deletes, and that one experiment runs end to end through Ollama with every mitigation
on. The run takes a few minutes on the VM; `--quick` skips it. It prints PASS or FAIL for each check and exits with 1
if any failed. It saves a draft named "Smoke test <time>" and deletes it again, so saved experiments are left as they were.

## Updating and maintenance

    git pull && docker compose up -d --build   # deploy new code
    python3 smoke_test.py https://<SITE_ADDRESS> --user <SITE_USER>   # check it works
    docker compose logs -f web                 # watch the web app's logs
    docker compose restart                     # restart everything

To change the password, put a new hash in `.env` and run `docker compose up -d`.

Saved experiments are in a SQLite database on the `experiments` Docker volume, so they survive rebuilds and `docker compose down`, but not `docker compose down -v`. Everyone who logs in sees the same saved experiments. To back them up:

    docker compose cp web:/data/experiments.db ./experiments-backup.db

- **Security updates:** Ubuntu installs them automatically. Rebuild now and then (`docker compose build --pull && docker compose up -d`) to update the base images.
- **Never set `FLASK_DEBUG=1` on the server.** Flask's debugger lets anyone who reaches the page run code on the machine.
- **Idle reclamation:** Oracle can reclaim a free VM whose CPU, network and memory use all stay under 20% for 7 days. The LLM container loads the model when it starts and keeps it in memory, which keeps memory use above that.
- **Speed:** each request takes up to a few minutes on 2 cores, depending on the input's length. `LLM_TIMEOUT` in `docker-compose.yml` sets how long each LLM call may take.
