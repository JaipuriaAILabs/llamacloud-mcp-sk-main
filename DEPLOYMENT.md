# Deploying LlamaCloud MCP Server to Render

This guide walks you through deploying the LlamaCloud MCP server to Render.

## Prerequisites

1. A [Render account](https://render.com) (free tier available)
2. A [LlamaCloud account](https://cloud.llamaindex.ai/)
3. LlamaCloud API key
4. Your LlamaCloud organization ID
5. At least one configured index or extract agent in LlamaCloud

## Configuration Format

This deployment supports **multiple indexes** with **per-index credentials**, allowing you to query indexes from different LlamaCloud accounts in a single deployment.

### Index Configuration Format

Each index is defined using the format:
```
index_name:description:api_key:org_id:project_id
```

**Example configurations:**

**Single Account (existing setup):**
- **Index Name**: AI-Strategy-Studies
- **Project Name**: Default
- **Organization ID**: 8d27cdab-b252-4a9b-a2c4-8eded34632a3
- **Transport**: streamable-http (HTTP-based MCP server)

**Multiple Accounts:**
You can now configure indexes from different LlamaCloud accounts by providing credentials per index.

## Deployment Steps

### Option 1: Deploy via Render Dashboard

1. **Create a New Web Service**
   - Go to your Render dashboard
   - Click "New +" → "Web Service"
   - Connect your GitHub repository

2. **Configure the Service**
   - **Name**: `llamacloud-mcp-server` (or your preferred name)
   - **Runtime**: Python 3
   - **Build Command**: `pip install -e .`
   - **Start Command**: `python start_server.py`

3. **Set Environment Variables**

   **For Multiple Indexes (Recommended):**

   Use numbered environment variables `INDEX_1`, `INDEX_2`, etc. Each index uses the format:
   `index_name:description:api_key:org_id:project_id`

   Example configuration with 3 indexes from 2 different accounts:

   ```
   INDEX_1=AI-Strategy-Studies:Search AI strategy research:llx-YOUR-KEY-1:8d27cdab-b252-4a9b-a2c4-8eded34632a3:Default
   INDEX_2=interim-primate-2026-01-21:Search case studies:llx-YOUR-KEY-2:6a9fda6c-fbd4-43f8-ad2b-4afbe41824d7:case-studies-supabase
   INDEX_3=Persuasion and communication OB:Persuasion and OB research:llx-YOUR-KEY-2:6a9fda6c-fbd4-43f8-ad2b-4afbe41824d7:case-studies-supabase
   TRANSPORT=streamable-http
   ```

   **For Single Index (Legacy, Backward Compatible):**

   - `INDEX_NAME`: `AI-Strategy-Studies`
   - `INDEX_DESCRIPTION`: `Search and retrieve information from AI Strategy Studies`
   - `LLAMA_CLOUD_API_KEY`: Your LlamaCloud API key (⚠️ Keep this secret!)
   - `PROJECT_NAME`: `Default`
   - `ORG_ID`: `8d27cdab-b252-4a9b-a2c4-8eded34632a3`
   - `TRANSPORT`: `streamable-http`

   ⚠️ **Security Note**: API keys in `INDEX_*` variables are secrets! Render's environment variables are encrypted at rest.

4. **Deploy**
   - Click "Create Web Service"
   - Render will automatically build and deploy your service

### Option 2: Deploy via render.yaml (Infrastructure as Code)

1. **Push to GitHub**
   ```bash
   git add .
   git commit -m "Add Render deployment configuration"
   git push
   ```

2. **Create Blueprint in Render**
   - Go to Render dashboard → "Blueprints"
   - Click "New Blueprint Instance"
   - Connect your repository
   - Render will automatically detect `render.yaml`
   - **Important**: Set the `LLAMA_CLOUD_API_KEY` as a secret environment variable in the Render dashboard (it's marked as `sync: false` for security)

3. **Deploy**
   - Review the configuration
   - Click "Apply"

## Post-Deployment

### Access Your MCP Server

Once deployed, your MCP server will be available at:
```
https://your-service-name.onrender.com
```

For streamable-http transport, the MCP endpoint will be:
```
https://your-service-name.onrender.com/mcp
```

### Testing the Server

You can test if the server is running by checking the health endpoint or connecting an MCP client.

### Using with Claude Desktop

To use this MCP server with Claude Desktop, update your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "llamacloud-render": {
      "command": "npx",
      "args": [
        "-y",
        "@modelcontextprotocol/client",
        "https://your-service-name.onrender.com/mcp"
      ]
    }
  }
}
```

## Monitoring and Logs

- **Logs**: View real-time logs in the Render dashboard under your service
- **Metrics**: Monitor CPU, memory usage, and request metrics
- **Auto-Deploy**: Render automatically redeploys when you push to your main branch

## Updating Configuration

### Adding or Removing Indexes

To add a new index from a different account:

1. Go to Render dashboard → Your service → Environment
2. Add a new variable: `INDEX_4=name:description:api_key:org_id:project_id`
3. The service will automatically restart and load the new index

To remove an index:

1. Delete the corresponding `INDEX_N` variable
2. The service will automatically restart

### Modifying Existing Indexes

To update index configuration:

1. Update the environment variables in the Render dashboard, OR
2. Modify `render.yaml` and push changes to trigger a redeployment

### Configuration Format Details

**Full format**: `name:description:api_key:org_id:project_id`

- All 5 fields required for per-index credentials
- Use this when indexes are from different LlamaCloud accounts
- Each index can have its own API key and organization ID

**Partial format with fallbacks**: `name:description`

- Uses default values from `LLAMA_CLOUD_API_KEY`, `ORG_ID`, `PROJECT_NAME`
- Only works if default credentials are configured
- Useful when all indexes are from the same account

## Troubleshooting

### Server won't start
- Check that `LLAMA_CLOUD_API_KEY` is set correctly
- Verify your organization ID and project name
- Check the logs in Render dashboard

### Port binding issues
- The server automatically uses Render's `PORT` environment variable
- Default port is 8000 if PORT is not set

### Index not found
- Verify the index name matches exactly (case-sensitive)
- Check that the index exists in your LlamaCloud project
- Verify organization ID and project ID are correct

## Security Notes

⚠️ **Never commit your API keys to the repository!**

- Use Render's environment variables for secrets
- The `LLAMA_CLOUD_API_KEY` in `render.yaml` is marked as `sync: false` to prevent accidental exposure
- Always set sensitive values through the Render dashboard

## Cost Considerations

- Render offers a free tier with limitations
- Consider upgrading to a paid plan for production use
- Web services on free tier may spin down after inactivity

## Next Steps

- Add more indexes by updating the environment variables
- Configure extract agents for document processing
- Set up custom domains
- Configure auto-scaling for production workloads
