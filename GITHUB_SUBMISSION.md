# Public GitHub submission

The assignment requires one public repository accessible without login. The target repository URL has not yet been provided, so no upload is claimed.

## Preserve the real history

The delivery ZIP includes ordinary project source plus `loyalty-rewards-history.bundle`, which preserves the actual incremental commits, including the test-driven fixes. Do **not** upload all files through GitHub's web uploader as a single final commit: that loses the development history.

With Git installed, extract the ZIP, open a terminal in its top-level folder and run:

```bash
git clone loyalty-rewards-history.bundle loyalty-rewards-with-history
cd loyalty-rewards-with-history
git remote remove origin
git remote add origin YOUR_PUBLIC_GITHUB_REPOSITORY_URL
git push -u origin main
```

Replace the placeholder with your new, empty repository URL. Create the GitHub repository as **Public**, without generating a README, license or `.gitignore` remotely. This avoids an unrelated initial history. If a repository already contains files, review and reconcile them rather than using a force push.

GitHub Desktop can open `loyalty-rewards-with-history` after cloning. Do not commit databases, code exports, real passwords or `.env` files. The bundle is only a delivery container and does not need to be uploaded into the repository.

## Verify before submitting

1. Check that `README.md`, `ASSUMPTIONS.md`, `AI_LOG.md`, `ARCHITECTURE.md`, `.env.example` and `tests/` are visible at repository root.
2. Open the Commits page: there should be multiple meaningful development commits.
3. Open the repository URL in a signed-out/private window. Confirm README and source are visible without login.
4. Clone into a clean folder and follow the README setup instructions.
5. Submit the repository URL, for example `https://github.com/YOUR_USERNAME/YOUR_REPOSITORY` (replace placeholders). Do not submit localhost or the ZIP as a substitute for the required URL.

The optional deployed application URL is separate from the required public repository URL. The app uses a backend; uploading to GitHub does not itself host a live running application.
