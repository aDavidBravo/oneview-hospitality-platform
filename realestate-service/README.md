# Real Estate Service

FastAPI microservice for the **Real Estate domain**.

## Endpoints

| Method | Path | Description |
|--------|------|-------------|
| GET | `/health` | Health check |
| GET | `/realestate/kpis/funnel?project_id=` | Funnel stage distribution |
| GET | `/realestate/kpis/conversion-rates?project_id=` | Conversion rates by stage |
| GET | `/realestate/kpis/revenue?project_id=` | Revenue & contract summary |
| GET | `/realestate/kpis/leads-by-channel?project_id=` | Leads & close rate by channel |
| GET | `/realestate/units/status?project_id=` | Units by type & status |
| GET | `/realestate/units/available?project_id=&unit_type=` | Available units |
| GET | `/realestate/projects/` | All projects with stats |
| GET | `/realestate/projects/{project_id}` | Single project detail |

## Quick Test

```bash
curl "http://localhost:8003/realestate/kpis/funnel?project_id=1"
curl "http://localhost:8003/realestate/units/status?project_id=1"
curl "http://localhost:8003/realestate/projects/"
```

## Interactive Docs

http://localhost:8003/docs
