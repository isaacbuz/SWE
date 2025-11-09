# Production Deployment Checklist

Use this checklist to ensure a successful production deployment.

## Pre-Deployment

### Code Quality
- [ ] All tests passing (unit, integration, e2e)
- [ ] Code coverage ≥ 80%
- [ ] No critical security vulnerabilities
- [ ] Performance tests passed
- [ ] Code review completed and approved
- [ ] Documentation updated

### Infrastructure
- [ ] Cloud resources provisioned
- [ ] Database configured and tested
- [ ] Redis configured and tested
- [ ] SSL certificates obtained and valid
- [ ] DNS records configured correctly
- [ ] Firewall rules configured
- [ ] Load balancer configured
- [ ] CDN configured (if applicable)

### Security
- [ ] All secrets stored securely
- [ ] Environment variables configured
- [ ] Security headers configured
- [ ] Rate limiting configured
- [ ] Authentication configured
- [ ] Authorization configured
- [ ] Audit logging enabled
- [ ] Security scanning completed

### Monitoring
- [ ] Monitoring tools configured
- [ ] Alerting rules configured
- [ ] Logging configured
- [ ] Dashboards created
- [ ] On-call rotation configured
- [ ] Incident response plan ready

## Deployment

### Preparation
- [ ] Backup current deployment
- [ ] Backup database
- [ ] Notify team of deployment
- [ ] Schedule maintenance window (if needed)
- [ ] Prepare rollback plan

### Deployment Steps
- [ ] Pull latest code
- [ ] Build Docker images
- [ ] Run database migrations
- [ ] Deploy services
- [ ] Verify health checks
- [ ] Run smoke tests
- [ ] Verify functionality

### Verification
- [ ] Health endpoints responding
- [ ] API endpoints working
- [ ] Authentication working
- [ ] Database connectivity verified
- [ ] Redis connectivity verified
- [ ] SSL certificates valid
- [ ] Monitoring active
- [ ] Logs accessible

## Post-Deployment

### Immediate Checks
- [ ] All services running
- [ ] No error logs
- [ ] Response times acceptable
- [ ] Error rates normal
- [ ] Resource usage normal

### Functional Testing
- [ ] User authentication works
- [ ] API endpoints respond correctly
- [ ] Tool execution works
- [ ] Frontend loads correctly
- [ ] External integrations work

### Performance Testing
- [ ] Smoke test passed
- [ ] Load test passed (if scheduled)
- [ ] Response times meet targets
- [ ] Throughput acceptable

### Security Testing
- [ ] Security headers present
- [ ] Rate limiting working
- [ ] Authentication secure
- [ ] No exposed secrets

## Monitoring (First 24 Hours)

### Hour 1
- [ ] Monitor error rates
- [ ] Check response times
- [ ] Verify resource usage
- [ ] Review logs for errors

### Hour 2-6
- [ ] Continue monitoring
- [ ] Check user feedback
- [ ] Verify all features working
- [ ] Monitor cost metrics

### Hour 6-24
- [ ] Review performance metrics
- [ ] Check for anomalies
- [ ] Verify backups running
- [ ] Document any issues

## Rollback Criteria

Rollback if:
- [ ] Critical errors in logs
- [ ] Error rate > 5%
- [ ] Response times > 2x baseline
- [ ] Service unavailable
- [ ] Security vulnerability discovered
- [ ] Data corruption detected

## Sign-Off

- [ ] Deployment completed successfully
- [ ] All checks passed
- [ ] Team notified
- [ ] Documentation updated
- [ ] Post-deployment review scheduled

---

**Deployment Date**: _______________  
**Deployed By**: _______________  
**Version**: _______________  
**Sign-Off**: _______________

