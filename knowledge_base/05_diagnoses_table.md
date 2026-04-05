# PHẦN 7: BẢNG CHẨN ĐOÁN CUỐI — 50 DIAGNOSES ĐẦY ĐỦ (FINAL v2.0)

---

## DIAG_PWR_01 — Adapter nguồn hỏng
```
mã:              DIAG_PWR_01
tên:             Adapter nguồn hỏng (Faulty Power Adapter)
nhóm:            power_startup
mức_độ:          HIGH (nguy cơ mất dữ liệu nếu laptop tắt đột ngột)
tự_xử_lý:       Có — mua adapter mới
cần_kỹ_thuật:    Không bắt buộc

triệu_chứng:
  - Không cắm điện thì máy không bật
  - Đèn sạc không sáng hoặc nhấp nháy
  - Adapter nóng bất thường hoặc có mùi khét
  - Pin không sạc dù cắm adapter

nguyên_nhân:
  - Dây adapter bị đứt bên trong
  - Bo mạch adapter bị hỏng
  - Cắm sai điện áp (110V vs 220V trên adapter cũ)
  - Adapter bị ngã/đổ nước

xử_lý_cơ_bản:
  1. Kiểm tra đèn LED trên adapter (nếu có)
  2. Thử ổ điện khác
  3. Kiểm tra đầu cắm adapter vào laptop không lỏng
  4. Mua adapter chính hãng thay thế

xử_lý_nâng_cao:
  - Đo điện áp adapter bằng đồng hồ vạn năng
  - Kiểm tra cổng sạc laptop (nếu adapter OK nhưng vẫn không sạc)

khi_nào_kỹ_thuật:
  - Nghi cổng sạc laptop bị hỏng (không phải adapter)
```

## DIAG_PWR_02 — Pin laptop chai/hỏng
```
mã:              DIAG_PWR_02
tên:             Pin laptop chai hoặc hỏng (Dead/Swollen Battery)
nhóm:            power_startup
mức_độ:          MEDIUM
tự_xử_lý:       Có — thay pin
cần_kỹ_thuật:    Không bắt buộc (nhưng khuyến nghị kỹ thuật thay pin)

triệu_chứng:
  - Máy chỉ chạy khi cắm điện
  - Pin ở 100% nhưng tắt ngay khi rút điện
  - Pin báo 0% và không tăng
  - Pin phồng (laptop lồi ở đáy)

nguyên_nhân:
  - Pin lithium suy giảm theo chu kỳ sạc (bình thường sau 2–4 năm)
  - Sạc không đúng cách (cắm điện 24/7)
  - Nhiệt độ cao làm pin lão hóa nhanh

xử_lý_cơ_bản:
  1. Battery report: cmd → powercfg /batteryreport
  2. Kiểm tra Design Capacity vs Full Charge Capacity
  3. Nếu xuống <80% → cân nhắc thay pin

xử_lý_nâng_cao:
  - Calibrate pin (xả về 0%, sạc 100% liên tục)
  - Thay pin chính hãng hoặc pin A-brand

cảnh_báo: Pin phồng → nguy hiểm → tháo ra ngay, KHÔNG sạc tiếp
```

## DIAG_PWR_03 — Nguồn máy bàn hỏng (PSU)
```
mã:              DIAG_PWR_03
tên:             Bộ nguồn máy bàn hỏng (Faulty PSU)
nhóm:            power_startup
mức_độ:          HIGH
tự_xử_lý:       Có (nếu biết lắp PSU)
cần_kỹ_thuật:    Khuyến nghị

triệu_chứng:
  - Desktop hoàn toàn không khởi động
  - Đèn LED bo mạch chủ không sáng
  - Nghe tiếng 'tạch' nhỏ nhưng không boot

nguyên_nhân:
  - Tụ điện PSU bị nổ
  - Cầu chì PSU bị đứt
  - Quá tải do linh kiện tiêu thụ nhiều điện

xử_lý_cơ_bản:
  1. Kiểm tra công tắc nguồn 115V/230V phía sau PSU
  2. Thử ổ điện khác
  3. Test PSU bằng paperclip test (short green + black wire on 24-pin)

xử_lý_nâng_cao:
  - Dùng PSU tester
  - Thay PSU mới, đảm bảo wattage đủ cho cấu hình

khi_nào_kỹ_thuật: Không chắc PSU hay bo mạch → cần kỹ thuật
```

## DIAG_PWR_04 — Bo mạch chủ lỗi điện
```
mã:              DIAG_PWR_04
tên:             Bo mạch chủ lỗi mạch điện (Motherboard Power Circuit Failure)
nhóm:            power_startup
mức_độ:          CRITICAL
tự_xử_lý:       Không
cần_kỹ_thuật:    Bắt buộc

triệu_chứng:
  - PSU hoạt động tốt nhưng máy vẫn không bật
  - Đèn LED bo mạch sáng nhưng không POST
  - Không nghe beep

nguyên_nhân:
  - Tụ điện bo mạch phồng/nổ
  - Lỗi mạch VRM (Voltage Regulator Module)
  - Vỡ socket CPU

xử_lý: Cần kỹ thuật viên — không thể tự sửa
chi_phí_ước_tính: Cao (thay bo mạch hoặc sửa IC VRM)
```

## DIAG_PWR_05 — RAM lỏng hoặc hỏng gây POST fail
```
mã:              DIAG_PWR_05
tên:             RAM lỏng hoặc hỏng gây POST thất bại
nhóm:            power_startup
mức_độ:          HIGH
tự_xử_lý:       Có — cắm lại RAM

triệu_chứng:
  - Nghe tiếng beep nhiều lần khi bật
  - Không lên màn hình sau POST beep lỗi
  - Đôi khi thay đổi số RAM ở BIOS

nguyên_nhân:
  - RAM bị lỏng (hay gặp sau khi di chuyển máy)
  - RAM bị bụi ở chân
  - RAM bị hỏng (chip RAM faulty)

xử_lý_cơ_bản:
  1. Tắt nguồn hoàn toàn, rút điện
  2. Mở máy, tháo RAM ra
  3. Dùng eraser (gôm chì) lau sạch chân RAM
  4. Cắm lại RAM, đảm bảo nghe tiếng "click"
  5. Thử với từng thanh RAM riêng lẻ

xử_lý_nâng_cao:
  - Chạy MemTest86 để kiểm tra RAM
  - Thay RAM nếu MemTest86 báo lỗi

khi_nào_kỹ_thuật: MemTest86 báo lỗi nhiều địa chỉ → mua RAM mới
```

---

## DIAG_DSP_01 — Cáp màn hình lỏng
```
mã:              DIAG_DSP_01
tên:             Cáp kết nối màn hình lỏng (Loose Display Cable/LVDS)
nhóm:            display
mức_độ:          MEDIUM
tự_xử_lý:       Có (laptop tháo lắp được)

triệu_chứng:
  - Màn hình đen đột ngột, đặc biệt khi di chuyển lid
  - Màn hình ngoài hoạt động bình thường
  - Đôi khi màn hình bật lại tạm thời

nguyên_nhân:
  - Cáp LVDS/eDP bị lỏng sau va chạm hoặc thời gian dài
  - Bản lề laptop làm mòn cáp theo thời gian

xử_lý_cơ_bản:
  1. Kết nối màn hình ngoài qua HDMI để xác nhận GPU OK
  2. Tháo cụm màn hình, kiểm tra cáp kết nối
  3. Cắm lại cáp LVDS/eDP cho chắc

xử_lý_nâng_cao:
  - Thay cáp màn hình nếu bị đứt bên trong

khi_nào_kỹ_thuật: Không quen mở laptop → kỹ thuật viên
```

## DIAG_DSP_02 — Driver card đồ họa lỗi
```
mã:              DIAG_DSP_02
tên:             Driver card đồ họa bị lỗi (GPU Driver Corrupted)
nhóm:            display
mức_độ:          MEDIUM
tự_xử_lý:       Có

triệu_chứng:
  - Màn hình nhấp nháy
  - Độ phân giải sai sau update
  - Lỗi xảy ra sau cài/update driver
  - Màn hình đen sau logo Windows

nguyên_nhân:
  - Driver GPU lỗi thời hoặc corrupt sau update Windows
  - Driver không tương thích với Windows version
  - File driver bị hỏng trong quá trình cài

xử_lý_cơ_bản:
  1. Boot vào Safe Mode
  2. Gỡ driver GPU qua Device Manager
  3. Tải driver chính hãng từ NVIDIA/AMD/Intel
  4. Cài lại driver mới

xử_lý_nâng_cao:
  - Dùng DDU (Display Driver Uninstaller) để xóa hoàn toàn
  - Rollback driver qua Device Manager > Driver > Roll Back
```

## DIAG_DSP_03 — Màn hình LCD hỏng
```
mã:              DIAG_DSP_03
tên:             Màn hình LCD/Panel bị hỏng (Defective LCD Panel)
nhóm:            display
mức_độ:          HIGH
tự_xử_lý:       Không khuyến nghị
cần_kỹ_thuật:    Bắt buộc

triệu_chứng:
  - Sọc thẳng đứng/ngang cố định
  - Màn hình trắng hoàn toàn
  - Backlight tắt (nhìn nghiêng thấy hình mờ)
  - Màn hình ngoài hoạt động bình thường

nguyên_nhân:
  - Va đập vật lý làm vỡ matrix LCD
  - Lỗi đèn nền (CCFL/LED backlight)
  - IC điều khiển trên panel hỏng

xử_lý:
  - Thay màn hình (panel) mới
  - Mang ra kỹ thuật viên, cung cấp model máy

chi_phí_ước_tính: Cao (2–5 triệu VND tùy laptop)
```

## DIAG_DSP_04 — Card đồ họa hỏng
```
mã:              DIAG_DSP_04
tên:             Card đồ họa rời bị hỏng (Discrete GPU Hardware Failure)
nhóm:            display
mức_độ:          CRITICAL
tự_xử_lý:       Không
cần_kỹ_thuật:    Bắt buộc

triệu_chứng:
  - Màu sắc bị méo, artifacts trên màn hình
  - Cả màn hình laptop và ngoài đều hiển thị sai
  - BSOD khi chạy game/ứng dụng đồ họa
  - Máy tắt đột ngột khi load GPU nặng

nguyên_nhân:
  - GPU overheating làm hỏng chip
  - Keo hàn (solder ball) bị nứt do nhiệt

xử_lý:
  - Reflow GPU (rủi ro cao)
  - Thay GPU (rất tốn kém với laptop)
  - Chuyển sang dùng iGPU nếu có
```

## DIAG_DSP_05 — Vấn đề độ sáng
```
mã:              DIAG_DSP_05
tên:             Độ sáng màn hình bị tắt hoặc cài sai
nhóm:            display
mức_độ:          LOW
tự_xử_lý:       Có

triệu_chứng:
  - Màn hình rất tối, gần như đen
  - Không phải hỏng phần cứng

xử_lý:
  1. Fn + brightness up key (F5/F6 tùy máy)
  2. Settings > Display > Brightness
  3. Kiểm tra adaptive brightness đang bật
```

---

## DIAG_OS_01 — Windows bị hỏng file hệ thống
```
mã:              DIAG_OS_01
tên:             File hệ thống Windows bị hỏng (System File Corruption)
nhóm:            os_boot
mức_độ:          HIGH
tự_xử_lý:       Có (nếu có USB Windows)

triệu_chứng:
  - OS treo ngẫu nhiên
  - Safe Mode hoạt động, Normal mode không
  - SFC/DISM báo lỗi
  - Boot chậm hoặc bị lỗi sau update

nguyên_nhân:
  - Mất điện đột ngột khi đang cập nhật
  - Malware phá file hệ thống
  - Bad sector trên HDD lưu file OS

xử_lý_cơ_bản:
  1. sfc /scannow (trong CMD elevated)
  2. DISM /Online /Cleanup-Image /RestoreHealth
  3. Restart và kiểm tra lại

xử_lý_nâng_cao:
  1. Boot từ USB Windows
  2. Chọn Repair → Troubleshoot → Startup Repair
  3. Nếu không được → Reset This PC (giữ files)

khi_nào_kỹ_thuật: Cần cài lại Windows hoàn toàn
```

## DIAG_OS_02 — Driver hoặc phần mềm gây BSOD
```
mã:              DIAG_OS_02
tên:             Driver hoặc phần mềm gây xung đột hệ thống
nhóm:            os_boot
mức_độ:          HIGH
tự_xử_lý:       Có

triệu_chứng:
  - BSOD với mã lỗi liên quan driver
  - Lỗi xuất hiện ngay sau cài driver/phần mềm mới
  - Safe Mode hoạt động bình thường

nguyên_nhân:
  - Driver không tương thích với Windows version
  - Phần mềm chạy ở kernel level gây conflict
  - Driver update từ Windows Update bị lỗi

xử_lý_cơ_bản:
  1. Boot Safe Mode → gỡ driver/phần mềm mới cài
  2. Device Manager → Roll back driver
  3. System Restore về điểm trước khi cài

xử_lý_nâng_cao:
  1. Phân tích minidump file (C:\Windows\Minidump)
  2. Dùng WinDbg để xác định driver gây lỗi
  3. Liên hệ nhà cung cấp driver

khi_nào_kỹ_thuật: Không xác định được driver gây lỗi
```

## DIAG_OS_03 — RAM lỗi gây BSOD
```
mã:              DIAG_OS_03
tên:             RAM bị lỗi gây màn hình xanh (Faulty RAM)
nhóm:            os_boot
mức_độ:          HIGH
tự_xử_lý:       Có (chạy test + thay RAM)

triệu_chứng:
  - BSOD ngẫu nhiên với mã MEMORY_MANAGEMENT
  - BSOD khi chạy ứng dụng sử dụng nhiều RAM
  - Máy treo ngẫu nhiên không có pattern

nguyên_nhân:
  - RAM chip bị lỗi (manufacturing defect hoặc aging)
  - RAM không đủ tốc độ/điện áp theo spec
  - RAM bị lỏng

xử_lý_cơ_bản:
  1. Windows Memory Diagnostic (mdsched.exe)
  2. MemTest86 (boot từ USB) — chạy ít nhất 2 passes
  3. Thử từng thanh RAM riêng lẻ

xử_lý_nâng_cao:
  - Thay RAM nếu MemTest86 báo lỗi
  - Kiểm tra XMP profile trong BIOS

khi_nào_kỹ_thuật: Lỗi RAM nhưng không tự thay được
```

## DIAG_OS_04 — HDD/SSD gây BSOD
```
mã:              DIAG_OS_04
tên:             HDD/SSD gây màn hình xanh (Storage Device Causing BSOD)
nhóm:            os_boot
mức_độ:          CRITICAL
tự_xử_lý:       Có (backup ngay!)

triệu_chứng:
  - BSOD với mã INACCESSIBLE_BOOT_DEVICE
  - BSOD với NTFS_FILE_SYSTEM
  - Máy không boot vào được Windows
  - HDD có tiếng kêu lạ

nguyên_nhân:
  - Bad sectors trên partition Windows
  - File system NTFS bị corrupt
  - Kết nối SATA lỏng

xử_lý_khẩn_cấp:
  1. **BACKUP DỮ LIỆU NGAY** (boot Linux Live USB)
  2. Chạy CHKDSK /f /r từ Recovery Console
  3. Crystal DiskInfo kiểm tra SMART data

xử_lý_dài_hạn:
  - Thay HDD/SSD nếu SMART báo lỗi
  - Cài lại Windows trên ổ mới

khi_nào_kỹ_thuật: Ổ đĩa hỏng phần cứng → kỹ thuật viên
```

## DIAG_OS_05 — Boot loop sau Windows Update
```
mã:              DIAG_OS_05
tên:             Vòng lặp khởi động sau Windows Update (Update Boot Loop)
nhóm:            os_boot
mức_độ:          HIGH
tự_xử_lý:       Có

triệu chứng:
  - Máy khởi động mãi, logo Windows xoay mãi không vào được
  - Xảy ra ngay sau cập nhật Windows
  - Không vào được Safe Mode bình thường

xử_lý_cơ_bản:
  1. Ngắt điện 3 lần → Windows tự vào WinRE
  2. WinRE → Uninstall Updates
  3. Hoặc: Startup Repair → Restore

xử_lý_nâng_cao:
  1. Boot USB Windows → Command Prompt
  2. wusa /uninstall /kb:XXXXXXX (mã KB của update lỗi)
  3. DISM để sửa image WinRE

khi_nào_kỹ_thuật: Không vào được WinRE → cần kỹ thuật reset
```

## DIAG_OS_06 — MBR/Boot Sector hỏng
```
mã:              DIAG_OS_06
tên:             MBR hoặc Boot Sector bị hỏng
nhóm:            os_boot
mức_độ:          HIGH
tự_xử_lý:       Có (cần USB Windows)

triệu_chứng:
  - "Operating system not found"
  - "BOOTMGR is missing"
  - "No bootable device"
  - Màn hình đen với con trỏ nhấp nháy

nguyên_nhân:
  - Malware hoặc rootkit xóa MBR
  - Mất điện khi ghi MBR
  - Cài thêm OS khác làm hỏng bootloader

xử_lý_cơ_bản:
  1. Boot từ USB Windows
  2. Recovery → Troubleshoot → Command Prompt
  3. bootrec /fixmbr
  4. bootrec /fixboot
  5. bootrec /rebuildbcd

khi_nào_kỹ_thuật: Các lệnh bootrec không hiệu quả
```

---

## DIAG_NET_01 — Driver Wi-Fi lỗi
```
mã:              DIAG_NET_01
tên:             Driver Wi-Fi bị lỗi (Wi-Fi Driver Problem)
nhóm:            network
mức_độ:          MEDIUM
tự_xử_lý:       Có

triệu_chứng:
  - Wi-Fi adapter thấy trong DM nhưng có dấu chấm than
  - Không thấy danh sách Wi-Fi dù adapter nhận
  - Wi-Fi chập chờn, ngắt kết nối liên tục

nguyên_nhân:
  - Driver không tương thích sau Windows Update
  - File driver bị corrupt

xử_lý_cơ_bản:
  1. Device Manager → Network Adapters → Wi-Fi → Update Driver
  2. Gỡ driver → Restart → Windows tự cài
  3. Tải driver từ website hãng laptop

xử_lý_nâng_cao:
  - Dùng cáp LAN để tải driver Wi-Fi đúng version
  - Rollback driver nếu lỗi sau update
```

## DIAG_NET_02 — Wi-Fi adapter hardware hỏng
```
mã:              DIAG_NET_02
tên:             Wi-Fi adapter phần cứng hỏng
nhóm:            network
mức_độ:          HIGH
tự_xử_lý:       Có thể (cắm USB Wi-Fi)

triệu_chứng:
  - Wi-Fi adapter không hiển thị trong Device Manager
  - Không thể bật Wi-Fi dù reinstall driver
  - Đèn Wi-Fi không sáng dù nhấn phím tắt

nguyên_nhân:
  - Card Wi-Fi M.2/PCIe bị hỏng
  - Va chạm làm đứt kết nối card
  - Card Wi-Fi bị disable ở BIOS

xử_lý_cơ_bản:
  1. Vào BIOS → kiểm tra Wi-Fi có bị disabled không
  2. Cắm USB Wi-Fi adapter như giải pháp tạm

xử_lý_nâng_cao:
  - Thay card Wi-Fi M.2 (2230 hoặc 2242)
  - Mang kỹ thuật nếu không quen thay card

chi_phí_ước_tính: Thấp–Trung (100–300k cho card M.2)
```

## DIAG_NET_03 — Lỗi DNS
```
mã:              DIAG_NET_03
tên:             Cấu hình DNS bị lỗi (DNS Configuration Error)
nhóm:            network
mức_độ:          LOW
tự_xử_lý:       Có

triệu_chứng:
  - Kết nối Wi-Fi nhưng không vào được website
  - Trình duyệt báo DNS_PROBE_FINISHED_NXDOMAIN
  - ping google.com không được nhưng ping 8.8.8.8 OK

nguyên_nhân:
  - DNS server tự động của ISP lỗi
  - DNS được cài tự động bị sai
  - Malware thay đổi DNS

xử_lý_cơ_bản:
  1. Settings → Network → Wi-Fi → Properties → IPv4
  2. Đổi DNS thành 8.8.8.8 / 8.8.4.4 (Google DNS)
  3. Hoặc 1.1.1.1 / 1.0.0.1 (Cloudflare DNS)
  4. Flush DNS: ipconfig /flushdns trong CMD
```

## DIAG_NET_04 — Router hoặc ISP lỗi
```
mã:              DIAG_NET_04
tên:             Vấn đề từ Router hoặc Nhà mạng (Router / ISP Issue)
nhóm:            network
mức_độ:          MEDIUM
tự_xử_lý:       Có (reset router)

triệu_chứng:
  - Tất cả thiết bị trong nhà đều không vào Internet
  - Router không có đèn Internet

nguyên_nhân:
  - Router firmware lỗi
  - Nhà mạng (ISP) bị sự cố
  - Quá tải kết nối IP

xử_lý_cơ_bản:
  1. Tắt Router 30 giây, bật lại
  2. Kiểm tra đèn trạng thái Router
  3. Gọi nhà mạng hỏi sự cố khu vực
  4. Thử kết nối hotspot điện thoại (bypass router)
```

## DIAG_NET_05 — Network Stack TCP/IP hỏng
```
mã:              DIAG_NET_05
tên:             Network Stack (TCP/IP) bị hỏng
nhóm:            network
mức_độ:          HIGH
tự_xử_lý:       Có (reset bằng lệnh CMD)

triệu_chứng:
  - Cả Wi-Fi và Ethernet đều không hoạt động
  - ipconfig /renew báo lỗi
  - Lỗi xảy ra sau khi cài phần mềm mạng hay VPN

nguyên_nhân:
  - Cài/gỡ VPN hoặc phần mềm mạng làm hỏng TCP/IP stack
  - Malware can thiệp vào mạng

xử_lý_cơ_bản: (CMD run as Admin)
  1. netsh winsock reset
  2. netsh int ip reset
  3. ipconfig /release
  4. ipconfig /flushdns
  5. ipconfig /renew
  6. Restart máy

khi_nào_kỹ_thuật: Sau reset vẫn lỗi → cài lại Windows
```

## DIAG_NET_06 — IP Conflict
```
mã:              DIAG_NET_06
tên:             Xung đột địa chỉ IP (IP Address Conflict)
nhóm:            network
mức_độ:          LOW
tự_xử_lý:       Có

triệu_chứng:
  - Thông báo "Address already in use"
  - ERR_NETWORK_CHANGED trong trình duyệt
  - Mạng ngắt kết nối rồi lại kết nối

nguyên_nhân:
  - Router cấp 2 thiết bị cùng IP (DHCP pool cạn)
  - Cài IP tĩnh bị trùng

xử_lý_cơ_bản:
  1. ipconfig /release → ipconfig /renew
  2. Đổi về DHCP tự động nếu đang dùng IP tĩnh
  3. Restart router
```

---

## DIAG_AUD_01 — Driver âm thanh lỗi
```
mã:              DIAG_AUD_01
tên:             Driver âm thanh bị lỗi (Audio Driver Problem)
nhóm:            audio_camera
mức_độ:          MEDIUM
tự_xử_lý:       Có

triệu_chứng:
  - Không có âm thanh
  - Thiết bị âm thanh có dấu chấm than trong DM
  - Âm thanh biến mất sau Windows Update

xử_lý_cơ_bản:
  1. Device Manager → Sound → Uninstall device
  2. Restart (Windows tự cài driver cơ bản)
  3. Tải driver từ Realtek/website hãng laptop

xử_lý_nâng_cao:
  - Rollback driver về version cũ
  - Dùng DDU xóa hoàn toàn rồi cài lại
```

## DIAG_AUD_02 — Âm thanh bị mute hoặc disable
```
mã:              DIAG_AUD_02
tên:             Âm thanh bị tắt hoặc thiết bị bị disable
nhóm:            audio_camera
mức_độ:          LOW
tự_xử_lý:       Có

triệu_chứng:
  - Volume bar hiển thị có nhưng không nghe thấy
  - Icon âm thanh có dấu gạch chéo đỏ

xử_lý:
  1. Right-click icon âm thanh → Open Sound Settings
  2. Kiểm tra Output device đúng chưa
  3. Playback Devices → Enable thiết bị âm thanh
  4. Volume mixer → kiểm tra từng app có bị mute không
```

## DIAG_AUD_03 — Phần cứng âm thanh hỏng
```
mã:              DIAG_AUD_03
tên:             Phần cứng loa hoặc soundcard bị hỏng
nhóm:            audio_camera
mức_độ:          HIGH
tự_xử_lý:       Không (cần thay phần cứng)

triệu_chứng:
  - Không thấy thiết bị âm thanh trong Device Manager
  - Cài lại driver vẫn không nhận
  - Âm thanh bị rè dù driver đúng

xử_lý:
  - Dùng loa/tai nghe USB ngoài như giải pháp tạm
  - Kỹ thuật viên kiểm tra jack audio hoặc soundcard
```

## DIAG_CAM_01 — Camera bị chặn bởi Privacy
```
mã:              DIAG_CAM_01
tên:             Camera bị chặn bởi cài đặt Privacy Windows
nhóm:            audio_camera
mức_độ:          LOW
tự_xử_lý:       Có

xử_lý:
  1. Settings → Privacy & Security → Camera
  2. Bật "Camera access" và "Let apps access your camera"
  3. Bật riêng cho từng app không nhận camera
```

## DIAG_CAM_02 — Driver camera lỗi
```
mã:              DIAG_CAM_02
tên:             Driver camera bị lỗi hoặc thiếu
nhóm:            audio_camera
mức_độ:          MEDIUM
tự_xử_lý:       Có

xử_lý:
  1. Device Manager → Cameras → Update/Reinstall driver
  2. Tải driver camera từ website hãng laptop
  3. Dùng Windows Update để tìm driver tự động
```

---

## DIAG_PER_01 — Cổng USB vật lý hỏng
```
mã:              DIAG_PER_01
tên:             Cổng USB bị hỏng vật lý
nhóm:            peripherals
mức_độ:          MEDIUM
tự_xử_lý:       Có (dùng cổng khác)

triệu_chứng:
  - Chỉ 1-2 cổng USB không nhận thiết bị
  - Thiết bị hoạt động tốt ở cổng khác / máy khác

giải_pháp_tạm:
  - Dùng cổng USB còn lại
  - USB hub có nguồn riêng

giải_pháp_dài_hạn:
  - Kỹ thuật viên thay cổng USB (hàn lại)
```

## DIAG_PER_02 — USB Controller driver lỗi
```
mã:              DIAG_PER_02
tên:             USB Controller driver bị lỗi
nhóm:            peripherals
mức_độ:          HIGH
tự_xử_lý:       Có

triệu_chứng:
  - Tất cả cổng USB đều không nhận thiết bị
  - Device Manager có lỗi ở USB Controller

xử_lý:
  1. Device Manager → Universal Serial Bus Controllers
  2. Uninstall tất cả USB controller entries
  3. Restart (Windows tự cài lại)
  4. Nếu không: cài lại chipset driver từ website hãng
```

## DIAG_PER_03 — Thiết bị USB hỏng
```
mã:              DIAG_PER_03
tên:             Thiết bị USB bị hỏng (Faulty USB Device)
nhóm:            peripherals
mức_độ:          MEDIUM
tự_xử_lý:       Có (thay thiết bị)

triệu_chứng:
  - Thiết bị không hoạt động trên nhiều máy, nhiều cổng
  - Đèn thiết bị không sáng khi cắm vào

xử_lý: Thay thiết bị USB mới
```

## DIAG_PER_04 — Driver thiết bị ngoại vi lỗi
```
mã:              DIAG_PER_04
tên:             Driver thiết bị ngoại vi bị thiếu hoặc lỗi
nhóm:            peripherals
mức_độ:          MEDIUM
tự_xử_lý:       Có

xử_lý:
  1. Device Manager → tìm Unknown Device / dấu chấm than
  2. Right-click → Update Driver → Search automatically
  3. Tải driver từ website nhà sản xuất thiết bị
```

---

## DIAG_PERF_01 — Thermal Throttling / Quá nhiệt
```
mã:              DIAG_PERF_01
tên:             CPU/GPU bị giảm xung do quá nhiệt (Thermal Throttling)
nhóm:            performance
mức_độ:          HIGH
tự_xử_lý:       Có (vệ sinh)

triệu_chứng:
  - Máy nóng, quạt chạy hết tốc độ
  - CPU tự giảm xuống 0.4–0.8 GHz (xem Task Manager)
  - HWMonitor báo nhiệt độ CPU >90°C
  - Hiệu năng giảm mạnh khi máy nóng

nguyên_nhân:
  - Bụi bịt kín hệ thống tản nhiệt
  - Keo tản nhiệt CPU/GPU đã cứng và mất tác dụng
  - Quạt quay chậm hoặc hỏng

xử_lý_cơ_bản:
  1. Dùng canned air thổi bụi qua lỗ thoáng
  2. Đặt máy trên bề mặt cứng, thoáng
  3. Dùng đế tản nhiệt (cooling pad)

xử_lý_nâng_cao:
  1. Tháo máy, vệ sinh hệ thống tản nhiệt
  2. Thay keo tản nhiệt (thermal paste)
  3. Kiểm tra quạt quay đúng tốc độ

khi_nào_kỹ_thuật: Không quen tháo máy → kỹ thuật viên vệ sinh
```

## DIAG_PERF_02 — Malware / Virus
```
mã:              DIAG_PERF_02
tên:             Máy bị nhiễm malware/virus gây chậm
nhóm:            performance
mức_độ:          HIGH
tự_xử_lý:       Có

triệu_chứng:
  - CPU cao dù không mở app gì
  - Process lạ trong Task Manager
  - Phần mềm diệt virus phát cảnh báo
  - Popup quảng cáo nhiều bất thường

xử_lý_cơ_bản:
  1. Chạy Windows Defender Full Scan
  2. Tải Malwarebytes (free) để quét thêm
  3. Boot vào Safe Mode → quét lại

xử_lý_nâng_cao:
  1. Kaspersky Rescue Disk (boot offline)
  2. Nếu không diệt được → cài lại Windows

khi_nào_kỹ_thuật: Malware quá sâu, cài lại Windows không xóa được
```

## DIAG_PERF_03 — Quá nhiều startup programs
```
mã:              DIAG_PERF_03
tên:             Quá nhiều chương trình khởi động cùng Windows
nhóm:            performance
mức_độ:          LOW
tự_xử_lý:       Có

triệu_chứng:
  - Boot mất 3–10 phút
  - Sau khi vào Windows, máy còn chậm thêm vài phút
  - Task Manager thấy nhiều app đang chạy ngầm

xử_lý:
  1. Task Manager → Startup tab
  2. Disable tất cả app không cần thiết
  3. msconfig → Services → Hide Microsoft Services → Disable others
  4. Settings → Apps → Startup → tắt app không cần
```

## DIAG_PERF_04 — RAM không đủ
```
mã:              DIAG_PERF_04
tên:             Dung lượng RAM không đủ cho tác vụ
nhóm:            performance
mức_độ:          MEDIUM
tự_xử_lý:       Có (nâng cấp RAM)

triệu_chứng:
  - RAM luôn >85% khi dùng bình thường
  - Máy chậm khi mở nhiều tab
  - Disk usage cao (Windows dùng Page File nhiều)

xử_lý_ngắn_hạn:
  1. Đóng app không dùng
  2. Tắt hiệu ứng visual của Windows
  3. Tắt Superfetch/SysMain service

xử_lý_dài_hạn:
  - Nâng cấp RAM (thêm 8–16GB)
  - Kiểm tra máy có khe RAM trống không
```

---

## DIAG_STR_01 — Ổ đĩa C: bị đầy
```
mã:              DIAG_STR_01
tên:             Ổ đĩa C: quá đầy gây ảnh hưởng hiệu năng
nhóm:            storage
mức_độ:          MEDIUM
tự_xử_lý:       Có

triệu_chứng:
  - Ổ C: < 10–20GB trống
  - Máy chậm, Windows Update thất bại
  - Không cài được phần mềm mới

xử_lý:
  1. Disk Cleanup (cleanmgr) → chọn System Files
  2. Settings → Apps → gỡ app ít dùng
  3. Di chuyển file nặng sang ổ D: hoặc ngoài
  4. WinDirStat để tìm file lớn bất thường
  5. Tắt Hibernation nếu không dùng: powercfg /h off
```

## DIAG_STR_02 — HDD đang hỏng
```
mã:              DIAG_STR_02
tên:             HDD cơ học đang bị hỏng (Failing HDD)
nhóm:            storage
mức_độ:          CRITICAL
tự_xử_lý:       Backup ngay — KHẨN CẤP

triệu_chứng:
  - Tiếng click lách cách khi HDD đọc/ghi
  - File biến mất hoặc bị hỏng
  - CHKDSK tìm thấy bad sectors
  - SMART data báo Reallocated Sectors > 0

cảnh_báo: HDD có tiếng click → nguy cơ mất dữ liệu trong vài giờ

xử_lý_khẩn_cấp:
  1. Backup TẤT CẢ dữ liệu ngay lập tức
  2. Dùng CrystalDiskInfo xem SMART status
  3. Nếu SMART "Caution" hoặc "Bad" → thay HDD ngay

xử_lý_sau:
  - Thay HDD mới hoặc SSD
  - Clone ổ cũ sang ổ mới nếu HDD còn đọc được
```

## DIAG_STR_03 — SSD suy giảm hiệu năng
```
mã:              DIAG_STR_03
tên:             SSD suy giảm hiệu năng hoặc sức khỏe thấp
nhóm:            storage
mức_độ:          MEDIUM–HIGH
tự_xử_lý:       Có (TRIM, hoặc thay SSD)

triệu_chứng:
  - CrystalDiskInfo báo health < 80%
  - Tốc độ đọc/ghi giảm mạnh so với ban đầu
  - Copy file chậm bất thường với SSD

nguyên_nhân:
  - SSD đã ghi nhiều (TBW gần limit)
  - TRIM không được kích hoạt
  - Firmware cũ

xử_lý:
  1. Kích hoạt TRIM: fsutil behavior query DisableDeleteNotify (0=OK)
  2. Cập nhật firmware SSD từ website hãng
  3. Tránh để SSD đầy > 90%
  4. Lên kế hoạch thay SSD mới nếu health < 50%
```

## DIAG_STR_04 — File system bị lỗi
```
mã:              DIAG_STR_04
tên:             File system NTFS bị lỗi (File System Corruption)
nhóm:            storage
mức_độ:          HIGH
tự_xử_lý:       Có

triệu_chứng:
  - File không mở được, báo lỗi
  - CHKDSK báo lỗi file system
  - Ổ đĩa thứ 2 không hiển thị trong Explorer

nguyên_nhân:
  - Mất điện đột ngột khi đang ghi dữ liệu
  - HDD có bad sectors ở vùng file system
  - Rút USB không đúng cách (eject)

xử_lý:
  1. Right-click ổ đĩa → Properties → Tools → Check
  2. CMD Admin: chkdsk C: /f /r /x
  3. Khởi động lại để chkdsk chạy trước khi Windows load
  4. Backup dữ liệu trước khi chkdsk
```
