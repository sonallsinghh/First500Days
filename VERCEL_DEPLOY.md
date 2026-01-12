# Vercel Deployment Guide

## Prerequisites

1. Install Vercel CLI (if deploying via CLI):
   ```bash
   npm i -g vercel
   ```

2. Ensure you have a Vercel account at https://vercel.com

## Deployment Steps

### Option 1: Deploy via Vercel Dashboard

1. Push your code to GitHub/GitLab/Bitbucket
2. Go to https://vercel.com/new
3. Import your repository
4. Vercel will auto-detect the Python project
5. Add environment variables (see below)
6. Deploy!

### Option 2: Deploy via CLI

1. Login to Vercel:
   ```bash
   vercel login
   ```

2. Deploy:
   ```bash
   vercel
   ```

3. For production:
   ```bash
   vercel --prod
   ```

## Environment Variables

Set these in your Vercel project settings (Settings → Environment Variables):

- `OPENAI_API_KEY` - Your OpenAI API key
- `HUGGINGFACE_API_KEY` - Your Hugging Face API token (with read permissions)

## Important Notes

1. **FAISS Index**: The `faiss_index/` directory must be included in your deployment. Make sure it's not in `.vercelignore`.

2. **File Size Limits**: 
   - Vercel has a 50MB limit for serverless functions
   - If your FAISS index is too large, consider:
     - Using a smaller index
     - Storing the index in cloud storage (S3, etc.) and loading it at runtime
     - Using Vercel's Pro plan for larger limits

3. **Cold Starts**: The first request after inactivity may be slower due to serverless cold starts.

4. **Timeout**: Vercel has execution time limits:
   - Hobby: 10 seconds
   - Pro: 60 seconds
   - Enterprise: 900 seconds

## Project Structure

```
.
├── api/
│   └── index.py          # Vercel serverless function entry point
├── app/                  # Your FastAPI application
├── faiss_index/          # FAISS vector index (must be included)
├── requirements.txt      # Python dependencies
├── vercel.json          # Vercel configuration
└── .vercelignore        # Files to exclude from deployment
```

## Testing Locally

You can test the Vercel deployment locally:

```bash
vercel dev
```

This will start a local server that mimics Vercel's environment.

## Troubleshooting

- **Import errors**: Make sure all dependencies are in `requirements.txt`
- **Missing files**: Check `.vercelignore` to ensure required files aren't excluded
- **Timeout errors**: Consider optimizing your code or upgrading your Vercel plan
- **Memory issues**: Vercel has memory limits; consider optimizing your FAISS index size

