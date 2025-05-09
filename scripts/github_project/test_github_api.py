#!/usr/bin/env python3
# -*- coding: utf-8 -*-

"""
GitHub GraphQL API测试脚本
"""

import json
import os

import requests

# 获取环境变量中的Token
token = os.environ.get("GITHUB_TOKEN")
if not token:
    print("错误: 环境变量GITHUB_TOKEN未设置")
    exit(1)

print(f"使用Token: {token[:4]}...{token[-4:]}")

# GraphQL端点
endpoint = "https://api.github.com/graphql"

# 测试查询 - 获取项目列表
query = """
query {
  viewer {
    login
    projectsV2(first: 10) {
      nodes {
        id
        title
        number
      }
    }
  }
}
"""

headers = {"Authorization": f"Bearer {token}", "Content-Type": "application/json"}

response = requests.post(endpoint, json={"query": query}, headers=headers)

print(f"\n状态码: {response.status_code}")

if response.status_code == 200:
    data = response.json()
    if "errors" in data:
        print("GraphQL错误:")
        for error in data["errors"]:
            print(f"  - {error.get('message')}")
    else:
        print("查询成功!")
        viewer = data.get("data", {}).get("viewer", {})
        login = viewer.get("login")
        projects = viewer.get("projectsV2", {}).get("nodes", [])

        print(f"\n用户: {login}")
        print(f"找到 {len(projects)} 个项目:")

        for project in projects:
            print(f"  - {project.get('title')} (#{project.get('number')}, ID: {project.get('id')})")

            # 测试使用ID获取项目
            project_id = project.get("id")
            project_number = project.get("number")

            if project_number == 3:
                print(f"\n尝试使用编号 #{project_number} 获取项目详情...")
                project_query = f"""
                query {{
                  viewer {{
                    projectV2(number: {project_number}) {{
                      title
                      id
                      number
                    }}
                  }}
                }}
                """

                project_response = requests.post(endpoint, json={"query": project_query}, headers=headers)

                print(f"状态码: {project_response.status_code}")
                if project_response.status_code == 200:
                    project_data = project_response.json()
                    if "errors" in project_data:
                        print("查询项目时出错:")
                        for error in project_data["errors"]:
                            print(f"  - {error.get('message')}")
                    else:
                        project_info = project_data.get("data", {}).get("viewer", {}).get("projectV2", {})
                        print(f"项目详情: {json.dumps(project_info, indent=2)}")
                else:
                    print(f"请求失败: {project_response.text}")

                # 使用Node ID获取项目
                print(f"\n尝试使用Node ID {project_id} 获取项目详情...")
                node_query = f"""
                query {{
                  node(id: "{project_id}") {{
                    ... on ProjectV2 {{
                      title
                      id
                      number
                    }}
                  }}
                }}
                """

                node_response = requests.post(endpoint, json={"query": node_query}, headers=headers)

                print(f"状态码: {node_response.status_code}")
                if node_response.status_code == 200:
                    node_data = node_response.json()
                    if "errors" in node_data:
                        print("查询节点时出错:")
                        for error in node_data["errors"]:
                            print(f"  - {error.get('message')}")
                    else:
                        node_info = node_data.get("data", {}).get("node", {})
                        print(f"节点详情: {json.dumps(node_info, indent=2)}")
                else:
                    print(f"请求失败: {node_response.text}")
else:
    print(f"请求失败: {response.text}")
