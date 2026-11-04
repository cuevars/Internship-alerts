# Internship Radar

Phone alerts for an NYIT CS sophomore seeking Summer 2027 cybersecurity, IT, data/analytics and other tech internships in NYC, New Jersey, Pennsylvania, or remote. Uses the public SimplifyJobs Summer2027 feed. No Python packages required; Python 3.11+.

## Try it now

```powershell
python radar.py --list
Start-Process .\matches.html
python -m unittest discover -s tests -v
```

`--list` downloads current matches and creates a readable shortlist without sending notifications or changing alert history. `--dry-run` prints matches without writing anything. Configuration is in `config.json`. NYC includes the boroughs and Long Island; NJ and PA include the whole state. Remote includes postings that say remote, so verify regional restrictions. Switch `include_remote` off if needed. Summer 2027 is an assumption you can change in `terms`.

## Connect your phone

1. Install **ntfy** on iPhone or Android: https://docs.ntfy.sh/subscribe/phone/
2. Generate a hard-to-guess topic on your computer: `python -c "import secrets; print('radar-' + secrets.token_hex(16))"`.
3. Subscribe to that exact topic on `https://ntfy.sh` in the phone app. Allow notifications.
4. In PowerShell, set `$env:NTFY_TOPIC = 'your-generated-topic'`, then run `python radar.py --test-notify`. Confirm it arrives on your phone.
5. Run `python radar.py` to start sending current matches, up to 15 per run. Later runs send only unseen jobs. To skip all current postings and watch only future matches, run `python radar.py --baseline` first instead.

Anyone who knows an unprotected public topic can read or publish to it. Use a random name; never send your résumé or personal information through it. For an authenticated topic, configure `NTFY_TOKEN` and the phone subscription with the appropriate account access. A custom HTTPS server can be set with `NTFY_SERVER` locally.

## Run while your computer is off

1. Create a GitHub repository and upload this project, including `.github/workflows/radar.yml` and the tests. A private repository keeps your shortlist/history private; check your account's Actions allowance.
2. Under Settings → Secrets and variables → Actions, add repository secret `NTFY_TOPIC` with the same topic. Add `NTFY_TOKEN` if using authentication.
3. Enable Actions and permit the workflow to write repository contents. Repository rules must allow the bot to push state commits to the default branch.
4. Under Actions → Internship Radar → Run workflow, run it once and confirm the phone alert. The schedule then requests runs every 30 minutes at minutes 7 and 37. GitHub scheduling can be delayed; this is not a guaranteed instant alert system. Public repositories can have scheduled workflows disabled after inactivity; monitor Actions status.
5. Download `internship-shortlist` from a workflow run to view the HTML report. Notifications link directly to each posting, so the report is optional on your phone.

Alert history is stored as `state.json` and committed by the workflow. Do not delete it unless you want old listings sent again. A delivery failure stops the run; successful sends are saved individually and pending jobs retry. A crash between sending and saving, or a failed Git push, can still cause a duplicate. Local state and generated reports are ignored by Git by default. If you create a local baseline before uploading, explicitly include that `state.json` to use it in GitHub.

## Your résumé workflow

Keep your master résumé and three versions (Cybersecurity, IT, Data) in Files, OneDrive or Google Drive on your phone. Each alert includes a role category, a relevant tailoring reminder, and the posting link. Open the posting, verify sophomore/graduation-year eligibility, work authorization, dates, and commute. Duplicate the closest résumé version, adjust your summary/skills/project bullets using truthful relevant experience, export a PDF such as `First_Last_Company.pdf`, then upload it in the employer's application. Record the job link, application date and résumé filename in your own tracker. The radar does not need access to your résumé to send alerts.

The feed does not reliably provide sophomore eligibility or full job descriptions. Track guidance is a starting point based on the title, not an AI review of the posting. The tool does not tailor or submit applications automatically. Feed coverage is incomplete and updates can lag employer websites; retain native job-board alerts for broader coverage. Degree filters exclude explicitly graduate-only entries but cannot guarantee eligibility. This version alerts on new IDs, not changes to an existing listing.

Sources: [feed repository](https://github.com/SimplifyJobs/Summer2027-Internships), [ntfy phone setup](https://docs.ntfy.sh/subscribe/phone/), [GitHub schedule behavior](https://docs.github.com/en/actions/reference/workflows-and-actions/events-that-trigger-workflows#schedule).
