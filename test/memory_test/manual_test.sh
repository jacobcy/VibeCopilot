#!/bin/bash
# VibeCopilot Memory命令手动测试脚本
# 此脚本提供交互式菜单，用于测试vc memory命令的各项功能

# 设置颜色
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
BLUE='\033[0;34m'
RESET='\033[0m'

# 设置测试文件夹和默认文件名
TEST_FOLDER="test_manual"
TEST_TITLE="test_note"
CURRENT_PATH=""

# 显示标题
show_header() {
    clear
    echo -e "${BLUE}====================================${RESET}"
    echo -e "${BLUE}  VibeCopilot Memory 命令手动测试  ${RESET}"
    echo -e "${BLUE}====================================${RESET}"
    echo ""
}

# 等待用户按键继续
wait_for_key() {
    echo ""
    echo -e "${YELLOW}按任意键继续...${RESET}"
    read -n 1
}

# 显示命令结果
show_result() {
    local cmd="$1"
    local title="$2"

    echo -e "${YELLOW}执行命令:${RESET} $cmd"
    echo -e "${YELLOW}$title:${RESET}"
    echo -e "${BLUE}--------------------------------${RESET}"
    eval "$cmd"
    local result=$?
    echo -e "${BLUE}--------------------------------${RESET}"

    if [ $result -eq 0 ]; then
        echo -e "${GREEN}命令执行成功${RESET}"
    else
        echo -e "${RED}命令执行失败 (返回码: $result)${RESET}"
    fi

    wait_for_key
}

# 创建笔记
create_note() {
    show_header
    echo -e "${YELLOW}创建笔记${RESET}"
    echo ""

    # 获取用户输入
    read -p "输入笔记标题 [默认: $TEST_TITLE]: " title
    title=${title:-$TEST_TITLE}

    read -p "输入存储目录 [默认: $TEST_FOLDER]: " folder
    folder=${folder:-$TEST_FOLDER}

    read -p "输入标签 (逗号分隔) [默认: 测试,manual]: " tags
    tags=${tags:-"测试,manual"}

    echo "输入笔记内容 (输入EOF结束):"
    content=""
    while IFS= read -r line; do
        [[ "$line" == "EOF" ]] && break
        content+="$line"$'\n'
    done

    # 保存笔记路径，用于后续操作
    CURRENT_PATH="$folder/$title"

    # 执行命令
    cmd="vibecopilot memory create --title \"$title\" --folder \"$folder\" --tags \"$tags\" --content \"$content\""
    show_result "$cmd" "创建笔记结果"
}

# 查看笔记
show_note() {
    show_header
    echo -e "${YELLOW}查看笔记${RESET}"
    echo ""

    # 如果没有当前笔记，询问路径
    if [ -z "$CURRENT_PATH" ]; then
        read -p "输入笔记路径 (如 folder/title): " path
        CURRENT_PATH=$path
    else
        echo -e "当前笔记路径: ${GREEN}$CURRENT_PATH${RESET}"
        read -p "使用其他路径? [y/N]: " change
        if [[ "$change" == "y" || "$change" == "Y" ]]; then
            read -p "输入笔记路径 (如 folder/title): " path
            CURRENT_PATH=$path
        fi
    fi

    # 执行命令
    cmd="vibecopilot memory show --path \"$CURRENT_PATH\""
    show_result "$cmd" "笔记内容"
}

# 更新笔记
update_note() {
    show_header
    echo -e "${YELLOW}更新笔记${RESET}"
    echo ""

    # 如果没有当前笔记，询问路径
    if [ -z "$CURRENT_PATH" ]; then
        read -p "输入笔记路径 (如 folder/title): " path
        CURRENT_PATH=$path
    else
        echo -e "当前笔记路径: ${GREEN}$CURRENT_PATH${RESET}"
        read -p "使用其他路径? [y/N]: " change
        if [[ "$change" == "y" || "$change" == "Y" ]]; then
            read -p "输入笔记路径 (如 folder/title): " path
            CURRENT_PATH=$path
        fi
    fi

    # 先显示当前内容
    echo -e "${YELLOW}当前内容:${RESET}"
    vibecopilot memory show --path "$CURRENT_PATH"

    # 获取新内容
    echo ""
    echo "输入更新后的内容 (输入EOF结束):"
    content=""
    while IFS= read -r line; do
        [[ "$line" == "EOF" ]] && break
        content+="$line"$'\n'
    done

    # 执行命令
    cmd="vibecopilot memory update --path \"$CURRENT_PATH\" --content \"$content\""
    show_result "$cmd" "更新笔记结果"
}

# 删除笔记
delete_note() {
    show_header
    echo -e "${YELLOW}删除笔记${RESET}"
    echo ""

    # 如果没有当前笔记，询问路径
    if [ -z "$CURRENT_PATH" ]; then
        read -p "输入笔记路径 (如 folder/title): " path
        CURRENT_PATH=$path
    else
        echo -e "当前笔记路径: ${GREEN}$CURRENT_PATH${RESET}"
        read -p "使用其他路径? [y/N]: " change
        if [[ "$change" == "y" || "$change" == "Y" ]]; then
            read -p "输入笔记路径 (如 folder/title): " path
            CURRENT_PATH=$path
        fi
    fi

    # 确认删除
    read -p "确认删除笔记 $CURRENT_PATH? [y/N]: " confirm
    if [[ "$confirm" != "y" && "$confirm" != "Y" ]]; then
        echo -e "${RED}操作已取消${RESET}"
        wait_for_key
        return
    fi

    # 执行命令
    cmd="vibecopilot memory delete --path \"$CURRENT_PATH\" --force"
    show_result "$cmd" "删除笔记结果"
    CURRENT_PATH=""
}

# 搜索笔记
search_notes() {
    show_header
    echo -e "${YELLOW}搜索笔记${RESET}"
    echo ""

    # 获取搜索关键词
    read -p "输入搜索关键词: " query
    if [ -z "$query" ]; then
        echo -e "${RED}未提供搜索关键词${RESET}"
        wait_for_key
        return
    fi

    # 执行命令
    cmd="vibecopilot memory search --query \"$query\""
    show_result "$cmd" "搜索结果"
}

# 列出笔记
list_notes() {
    show_header
    echo -e "${YELLOW}列出笔记${RESET}"
    echo ""

    # 询问是否筛选目录
    read -p "筛选特定目录? [y/N]: " filter
    if [[ "$filter" == "y" || "$filter" == "Y" ]]; then
        read -p "输入目录名: " folder
        cmd="vibecopilot memory list --folder \"$folder\""
    else
        cmd="vibecopilot memory list"
    fi

    # 执行命令
    show_result "$cmd" "笔记列表"
}

# 同步知识库
sync_memory() {
    show_header
    echo -e "${YELLOW}同步知识库${RESET}"
    echo ""

    # 执行命令
    cmd="vibecopilot memory sync"
    show_result "$cmd" "同步结果"
}

# 主菜单
main_menu() {
    while true; do
        show_header
        echo -e "当前操作笔记: ${GREEN}${CURRENT_PATH:-未选择}${RESET}"
        echo ""
        echo -e "可用操作:"
        echo -e "  ${BLUE}1.${RESET} 创建笔记"
        echo -e "  ${BLUE}2.${RESET} 查看笔记"
        echo -e "  ${BLUE}3.${RESET} 更新笔记"
        echo -e "  ${BLUE}4.${RESET} 删除笔记"
        echo -e "  ${BLUE}5.${RESET} 搜索笔记"
        echo -e "  ${BLUE}6.${RESET} 列出笔记"
        echo -e "  ${BLUE}7.${RESET} 同步知识库"
        echo -e "  ${BLUE}0.${RESET} 退出"
        echo ""
        read -p "选择操作 [0-7]: " choice

        case $choice in
            1) create_note ;;
            2) show_note ;;
            3) update_note ;;
            4) delete_note ;;
            5) search_notes ;;
            6) list_notes ;;
            7) sync_memory ;;
            0)
                echo -e "${GREEN}测试完成，感谢使用！${RESET}"
                exit 0
                ;;
            *)
                echo -e "${RED}无效选择，请重试${RESET}"
                wait_for_key
                ;;
        esac
    done
}

# 运行主菜单
main_menu
