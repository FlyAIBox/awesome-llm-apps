#!/bin/bash

# 脚本名称: set_bashrc_env.sh
# 脚本功能: 在用户的 ~/.bashrc 文件中设置或更新环境变量。
#           如果变量已存在，则会先删除旧的设置，然后添加新的。

# 使用方法:
#   ./set_bashrc_env.sh <变量名> <变量值>
#
# 示例:
#   # 设置一个不含空格的变量值
#   ./set_bashrc_env.sh MY_NEW_VAR my_simple_value
#
#   # 设置一个包含空格的变量值 (请用双引号括起来)
#   ./set_bashrc_env.sh ANOTHER_VAR "this is my value with spaces"
#
#   # 更新 OpenAI API 相关的 URL 环境变量
#   ./set_bashrc_env.sh OPENAI_API_BASE "https://vip.apiyi.com/v1"
#   ./set_bashrc_env.sh OPENAI_BASE_URL "https://vip.apiyi.com/v1"
#
# 前置条件:
#   - 确保 ~/.bashrc 文件存在且有写入权限。如果不存在，脚本会尝试创建它。
#
# 执行步骤:
# 1. 保存脚本: 将此代码保存为 set_bashrc_env.sh 文件。
# 2. 添加执行权限: 在终端运行 'chmod +x set_bashrc_env.sh'。
# 3. 运行脚本: 按照上述使用方法执行脚本。
# 4. 使更改生效: 脚本执行后，你需要运行 'source ~/.bashrc'
#    或关闭并重新打开终端，以使新的环境变量在当前会话中生效。

# 检查是否提供了正确的参数数量
if [ "$#" -ne 2 ]; then
    echo "错误：参数数量不正确。"
    echo "使用方法: $0 <变量名> <变量值>"
    echo "示例: $0 MY_VARIABLE \"my_value_with_spaces\""
    exit 1
fi

VARIABLE_NAME="$1"
VARIABLE_VALUE="$2"
BASHRC_FILE="$HOME/.bashrc"

echo "--- 正在设置环境变量 ---"
echo "变量名: ${VARIABLE_NAME}"
echo "变量值: ${VARIABLE_VALUE}"
echo "------------------------"

# 检查 .bashrc 文件是否存在，如果不存在则创建
if [ ! -f "${BASHRC_FILE}" ]; then
    touch "${BASHRC_FILE}"
    echo "注意: '${BASHRC_FILE}' 文件不存在，已为您创建。"
fi

# 检查 .bashrc 文件是否有写入权限
if [ ! -w "${BASHRC_FILE}" ]; then
    echo "错误: '${BASHRC_FILE}' 文件没有写入权限。请检查文件权限。"
    exit 1
fi

# 确保删除旧的变量设置行
# 这里的sed命令会删除所有以 "export VARIABLE_NAME=" 开头的行
# 或者只是 "VARIABLE_NAME=" 但后面没有 "export" 的行
# 并且删除所有以 "unset VARIABLE_NAME" 开头的行
sed -i "/^export ${VARIABLE_NAME}=/d; /^${VARIABLE_NAME}=/d; /^unset ${VARIABLE_NAME}/d" "${BASHRC_FILE}"

# 添加新的变量设置
echo "" >> "${BASHRC_FILE}"
echo "# Added by set_bashrc_env.sh on $(date)" >> "${BASHRC_FILE}"
echo "export ${VARIABLE_NAME}=\"${VARIABLE_VALUE}\"" >> "${BASHRC_FILE}"
echo "" >> "${BASHRC_FILE}" # 添加一个空行以保持格式整洁

echo "环境变量 '${VARIABLE_NAME}' 已更新到 '${BASHRC_FILE}'。"
echo "请运行 'source ${BASHRC_FILE}' 或重启终端以使更改生效。"
echo "请运行 'echo ${VARIABLE_NAME}' 查看变量值是否生效。"
exit 0