echo MERO_STB_USB_SCRIPT_002_START
sleep 12; echo MERO_P2_DELAY_DONE
version; echo MERO_P2_VERSION_DONE
printenv bootcmd bootargs; echo MERO_P2_ENV_DONE
setenv mero_p2_ip ${ipaddr}
setenv mero_p2_mask ${netmask}
setenv mero_p2_retry ${netretry}
setenv ipaddr 192.168.1.134
setenv netmask 255.255.255.0
setenv netretry no
echo MERO_STB_USB_SCRIPT_002_PING_1
ping 192.168.1.97; echo MERO_P2_PING_DONE
sleep 3; echo MERO_P2_GAP_DONE
echo MERO_STB_USB_SCRIPT_002_PING_2
ping 192.168.1.97; echo MERO_P2_PING_DONE
sleep 7; echo MERO_P2_GAP_DONE
echo MERO_STB_USB_SCRIPT_002_PING_3
ping 192.168.1.97; echo MERO_P2_PING_DONE
setenv ipaddr ${mero_p2_ip}
setenv netmask ${mero_p2_mask}
setenv netretry ${mero_p2_retry}
setenv mero_p2_ip
setenv mero_p2_mask
setenv mero_p2_retry
echo MERO_STB_USB_SCRIPT_002_END
