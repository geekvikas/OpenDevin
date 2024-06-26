import asyncio
import argparse
import sys
from typing import Type

import agenthub  # noqa F401 (we import this to get the agents registered)
from opendevin import config
from opendevin.schema import ConfigType
from opendevin.agent import Agent
from opendevin.controller import AgentController
from opendevin.llm.llm import LLM


def read_task_from_file(file_path: str) -> str:
    """Read task from the specified file."""
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def read_task_from_stdin() -> str:
    """Read task from stdin."""
    return sys.stdin.read()


def parse_arguments():
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description='Run an agent with a specific task')
    parser.add_argument(
        '-d',
        '--directory',
        type=str,
        help='The working directory for the agent',
    )
    parser.add_argument(
        '-t', '--task', type=str, default='', help='The task for the agent to perform'
    )
    parser.add_argument(
        '-f',
        '--file',
        type=str,
        help='Path to a file containing the task. Overrides -t if both are provided.',
    )
    parser.add_argument(
        '-c',
        '--agent-cls',
        default='MonologueAgent',
        type=str,
        help='The agent class to use',
    )
    parser.add_argument(
        '-m',
        '--model-name',
        default=config.get(ConfigType.LLM_MODEL),
        type=str,
        help='The (litellm) model name to use',
    )
    parser.add_argument(
        '-i',
        '--max-iterations',
        default=config.get(ConfigType.MAX_ITERATIONS),
        type=int,
        help='The maximum number of iterations to run the agent',
    )
    parser.add_argument(
        '-n',
        '--max-chars',
        default=config.get(ConfigType.MAX_CHARS),
        type=int,
        help='The maximum number of characters to send to and receive from LLM per task',
    )
    args, _ = parser.parse_known_args()
    return args


async def main():
    """Main coroutine to run the agent controller with task input flexibility."""
    args = parse_arguments()

    # Determine the task source
    if args.file:
        task = read_task_from_file(args.file)
    elif args.task:
        task = args.task
    elif not sys.stdin.isatty():
        task = read_task_from_stdin()
    else:
        raise ValueError(
            'No task provided. Please specify a task through -t, -f.')

    print(
        f'Running agent {args.agent_cls} (model: {args.model_name}, directory: {args.directory}) with task: "{task}"'
    )
    llm = LLM(args.model_name)
    AgentCls: Type[Agent] = Agent.get_cls(args.agent_cls)
    agent = AgentCls(llm=llm)
    controller = AgentController(
        agent=agent, max_iterations=args.max_iterations, max_chars=args.max_chars
    )

    await controller.start_loop(task)


if __name__ == '__main__':
    asyncio.run(main())
