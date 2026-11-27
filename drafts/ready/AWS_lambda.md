# AWS Lambda doubles on-demand timeout to 30 minutes and adds graphics processor instances
type: report
then: Until November 19, 2026, AWS Lambda Event Functions had a 15-minute timeout, apart from asynchronous and event source mapping invocations on Lambda Managed Instances, which Amazon Web Services extended to 90 minutes in September 2026 [AWS Compute Blog](https://aws.amazon.com/blogs/compute/announcing-30-minute-timeout-for-on-demand-aws-lambda-event-functions/).
now: Amazon Web Services stated in its weekly roundup that any Event Function can now be configured with a timeout of up to 30 minutes (1,800 seconds), and that its new graphics processor support runs on G-series instances from G4dn to G6e [AWS Weekly Roundup](https://aws.amazon.com/blogs/aws/aws-weekly-roundup-local-zone-in-bogota-30-minute-lambda-timeout-and-more-november-24-2026/).
summary: Amazon Web Services doubled the AWS Lambda on-demand timeout to 30 minutes and added graphics processor instances to Lambda Managed Instances.

Amazon Web Services announced on November 19, 2026, that AWS Lambda Event Functions running on demand can now run for up to 30 minutes (1,800 seconds), doubling the previous 15-minute limit for synchronous, asynchronous and event source mapping invocations [AWS Compute Blog](https://aws.amazon.com/blogs/compute/announcing-30-minute-timeout-for-on-demand-aws-lambda-event-functions/). The longer timeout is available in all commercial Amazon Web Services Regions, and synchronous invocations on Lambda Managed Instances now carry the same 30-minute limit [AWS Compute Blog](https://aws.amazon.com/blogs/compute/announcing-30-minute-timeout-for-on-demand-aws-lambda-event-functions/). On November 18, 2026, the company announced the general availability of Amazon EC2 G-series graphics processor instances for Event Functions on Lambda Managed Instances, supporting G4dn, G5, G6, G6f, Gr6, Gr6f and G6e [AWS News Blog](https://aws.amazon.com/blogs/aws/aws-lambda-now-supports-gpu-instances-for-event-functions-on-lambda-managed-instances/).

## Key Facts

| Item | Detail | Source |
|---|---|---|
| On-demand Event Function timeout | Up to 30 minutes (1,800 seconds) for synchronous, asynchronous and event source mapping invocations in all commercial Amazon Web Services Regions | [AWS Compute Blog](https://aws.amazon.com/blogs/compute/announcing-30-minute-timeout-for-on-demand-aws-lambda-event-functions/) |
| Lambda Managed Instances timeouts | Synchronous invocations up to 30 minutes; asynchronous and event source mapping invocations up to 90 minutes | [AWS Compute Blog](https://aws.amazon.com/blogs/compute/announcing-30-minute-timeout-for-on-demand-aws-lambda-event-functions/) |
| Supported graphics processor instances | Amazon EC2 G-series: G4dn, G5, G6, G6f, Gr6, Gr6f and G6e | [AWS News Blog](https://aws.amazon.com/blogs/aws/aws-lambda-now-supports-gpu-instances-for-event-functions-on-lambda-managed-instances/) |
| Accelerator memory | AcceleratorMemorySize supports 3, 6, 12, 16, 24 and 48 gigabytes | [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-gpu-troubleshooting.html) |
| Pricing | Standard Amazon EC2 instance pricing, a compute management fee of 9.75 per cent for G-series graphics processor instance types (15 per cent for central processing unit instance types) and $0.20 per million requests | [AWS Lambda pricing](https://aws.amazon.com/lambda/pricing/) |
| Default graphics processor utilization target | 40 per cent, designed to leave headroom for traffic to double within five minutes | [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-gpu-scaling.html) |

## Timeline

- **2026-11-18**: Amazon Web Services announced G-series graphics processor instances for Lambda Managed Instances ([AWS News Blog](https://aws.amazon.com/blogs/aws/aws-lambda-now-supports-gpu-instances-for-event-functions-on-lambda-managed-instances/)).
- **2026-11-19**: Amazon Web Services raised the on-demand Event Function timeout to 30 minutes (1,800 seconds) ([AWS Compute Blog](https://aws.amazon.com/blogs/compute/announcing-30-minute-timeout-for-on-demand-aws-lambda-event-functions/)).
- **2026-11-24**: The AWS Weekly Roundup recapped both Lambda releases ([AWS Weekly Roundup](https://aws.amazon.com/blogs/aws/aws-weekly-roundup-local-zone-in-bogota-30-minute-lambda-timeout-and-more-november-24-2026/)).

## Details (as Reported)

- The AWS News Blog lists the base images `base:cuda`, `cupy:cuda`, `pytorch:cuda`, `vllm:cuda` and `sglang:cuda`, and states that functions accelerated by graphics processors are deployed as Open Container Initiative container images, with images of up to 32 gigabytes and up to 32 gigabytes of Non-Volatile Memory Express ephemeral storage in /tmp [AWS News Blog](https://aws.amazon.com/blogs/aws/aws-lambda-now-supports-gpu-instances-for-event-functions-on-lambda-managed-instances/).
- The post also asks customers to request an increase to their G-series instance quota, listed as Running On-Demand G and VT instances, because new accounts might start with a quota of 0 [AWS News Blog](https://aws.amazon.com/blogs/aws/aws-lambda-now-supports-gpu-instances-for-event-functions-on-lambda-managed-instances/).
- The AWS Compute Blog states that a 25-minute inference run that fails at minute 22 restarts from zero without checkpoints, but resumes from its last checkpoint with Lambda durable functions [AWS Compute Blog](https://aws.amazon.com/blogs/compute/announcing-30-minute-timeout-for-on-demand-aws-lambda-event-functions/).
- According to the same post, Kafka event source mappings created before November 19, 2026 that do not use provisioned mode remain limited to 14 minutes (840 seconds) unless customers create a new mapping or turn on provisioned mode [AWS Compute Blog](https://aws.amazon.com/blogs/compute/announcing-30-minute-timeout-for-on-demand-aws-lambda-event-functions/).
- The Lambda documentation states that scaling from zero can take several minutes while Lambda provisions new graphics processor instances, and that requests might fail if capacity is not available [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-gpu-scaling.html).
- The documentation adds that Lambda uses reserved capacity automatically when On-Demand Capacity Reservations are created with open instance eligibility, and that Lambda Managed Instances does not support targeted reservations [AWS Lambda documentation](https://docs.aws.amazon.com/lambda/latest/dg/lambda-managed-instances-gpu-scaling.html).

## What Is Not Yet Confirmed

The sources do not list open questions.
