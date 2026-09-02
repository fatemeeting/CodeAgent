"""plan.py 单元测试：任务规划 + CLI --plan 交互确认（mock，免 key）。"""

from unittest import mock

from agent.plan import make_plan


def _response(content):
    msg = mock.Mock()
    msg.content = content
    msg.tool_calls = None
    choice = mock.Mock()
    choice.message = msg
    resp = mock.Mock()
    resp.choices = [choice]
    return resp


def test_make_plan_returns_content():
    client = mock.Mock()
    client.chat.return_value = _response("1. 创建文件\n2. 运行验证")
    out = make_plan(client, "创建并运行脚本")
    assert out == "1. 创建文件\n2. 运行验证"
    client.chat.assert_called_once()


def test_make_plan_with_feedback():
    """修改意见必须进入规划提示词。"""
    client = mock.Mock()
    client.chat.return_value = _response("1. 先写测试\n2. 实现")
    out = make_plan(client, "实现登录", feedback="先写测试再实现")
    assert out == "1. 先写测试\n2. 实现"
    sent = client.chat.call_args[0][0][1]["content"]
    assert "修改意见" in sent and "先写测试再实现" in sent


def _config():
    from agent.config import Config

    return Config(api_key="k", base_url="https://example.com", model="deepseek-chat", max_iterations=3)


def test_cli_plan_interactive_confirm():
    """--plan：输入修改意见重新生成 → 确认 y → 注入已确认计划执行。"""
    from agent import cli

    plans = iter(["1. 步骤A", "1. 步骤B（修改后）"])
    with mock.patch("agent.cli.Config.from_env", return_value=_config()), mock.patch(
        "agent.cli.make_plan", side_effect=lambda c, t, feedback=None: next(plans)
    ), mock.patch("agent.cli.run", return_value="完成") as run_mock, mock.patch(
        "builtins.input", side_effect=["先写测试再实现", "y"]
    ):
        rc = cli.main(["实现登录", "--plan"])
    assert rc == 0
    task_arg = run_mock.call_args[0][1]
    assert "已确认的执行计划" in task_arg
    assert "步骤B" in task_arg  # 修改后的计划被注入


def test_cli_plan_interactive_cancel():
    """--plan：n 取消 → 不执行。"""
    from agent import cli

    with mock.patch("agent.cli.Config.from_env", return_value=_config()), mock.patch(
        "agent.cli.make_plan", return_value="1. 步骤"
    ), mock.patch("agent.cli.run") as run_mock, mock.patch("builtins.input", side_effect=["n"]):
        rc = cli.main(["实现登录", "--plan"])
    assert rc == 0
    run_mock.assert_not_called()


def test_cli_plan_eof_cancels():
    """--plan：非交互（EOF）视为取消 → 不执行。"""
    from agent import cli

    with mock.patch("agent.cli.Config.from_env", return_value=_config()), mock.patch(
        "agent.cli.make_plan", return_value="1. 步骤"
    ), mock.patch("agent.cli.run") as run_mock, mock.patch(
        "builtins.input", side_effect=EOFError
    ):
        rc = cli.main(["实现登录", "--plan"])
    assert rc == 0
    run_mock.assert_not_called()
