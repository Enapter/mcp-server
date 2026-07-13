import uuid

from enapter_mcp_server import core, domain, fake


class Policy(fake.DefaultPolicy):
    async def create_rule(
        self,
        state: fake.State,
        auth: core.AuthConfig,
        site_id: str,
        slug: str,
        script: domain.RuleScript,
        disabled: bool,
    ) -> domain.Rule:
        for rule in state.rules:
            if rule.slug == slug:
                raise core.RuleSlugConflict(
                    slug=slug,
                    site_id=site_id,
                )
        rule = domain.Rule(
            id=uuid.uuid4().hex,
            slug=slug,
            disabled=disabled,
            state=(
                domain.RuleState.STARTED if not disabled else domain.RuleState.STOPPED
            ),
            script=script,
        )
        state.rules.append(rule)
        return rule
