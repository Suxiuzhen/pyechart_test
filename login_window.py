
import wmi

'''
被登陆电脑需在网络属性-共享中开启，允许其他网络用户通过此计算机的Internet来连接
'''

username = "Admin"
password = "yusi1437"
domain = "10.0.0.185"
command = "dir c:"


def main():
    # 创建WMI连接
    c = wmi.WMI(computer=domain, user=username, password=password, impersonation_level="impersonate")

    # 使用WMI执行命令
    process_startup = c.Win32_ProcessStartup.new()
    process_startup.ShowWindow = 1
    process_id, result = c.Win32_Process.Create(
        CommandLine=command,
        ProcessStartupInformation=process_startup
    )

    # 输出命令执行结果
    print("Return value:", result)
    if result != 0:
        raise f'命令执行失败! : {command}'

    # 注销登录
    # c.Win32_OperatingSystem()[0].Win32Shutdown(0x4)


if __name__ == '__main__':
    main()
