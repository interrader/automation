# Image Processing Automation

Generic technical workflow to download a completed Creatomate PNG render and normalize its outline to #1F1F1F with transparent background. Preview background: #ECECEC.

## Setup
1. Upload the contents of this directory to the root of your GitHub repository, preserving `.github/workflows/process-image.yml`. Do not upload the ZIP itself.
2. Under repository Settings > Actions > General > Workflow permissions, allow Read and write permissions if needed. The workflow also declares `permissions: contents: write`.
3. Under Actions > Process Image > Run workflow, enter a completed Creatomate PNG URL and an asset name such as `sample_01`.
4. On success, `assets/sample_01.png` (transparent), `assets/sample_01_preview.png`, `assets/sample_01_source.png` and `assets/sample_01.json` are committed to the repository. These are public in a public repository.
5. Use `https://raw.githubusercontent.com/OWNER/automation/main/assets/sample_01.png` as the image URL after replacing OWNER and confirming the default branch name.

## Limits
- Manual Actions trigger for this pilot; not end-to-end automatic yet.
- Only PNG URLs from the allowlisted Creatomate storage host are accepted.
- Automatic white-background removal requires a genuinely white background and may erase white details.
- Cannot guarantee removal of unwanted objects, line-art quality or anatomical correctness.
- Never put secrets, unpublished confidential imagery or proprietary prompts into a public repository.
