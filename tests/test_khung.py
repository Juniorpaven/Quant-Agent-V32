"""Kiểm thử tự động cho khung backtest và quy tắc không nhìn trước tương lai (dữ liệu giả lập, không cần mạng)."""
import os, sys, unittest
import numpy as np, pandas as pd
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "v34"))
import khung_backtest as kb


def gia_gia_lap(n=400, mu=0.0004, sd=0.01, seed=3):
    rng = np.random.default_rng(seed); ng = pd.bdate_range("2020-01-01", periods=n)
    def mk(p0):
        c = p0 * np.exp(np.cumsum(rng.normal(mu, sd, n))); o = np.r_[c[0], c[:-1]]
        return pd.DataFrame({"Open": o, "High": np.maximum(o, c), "Low": np.minimum(o, c), "Close": c, "Volume": np.full(n, 5e6)}, index=ng)
    return {"VNINDEX": mk(800), "E1VFVN30": mk(20), "AAA": mk(30)}


class MuaMotLan:
    """Mua E1VFVN30 vào phiên đầu rồi muốn bán ngay phiên sau."""
    def __init__(self): self.i = 0
    def muc_tieu(self, eng, i, vi_the, tien, nav):
        self.i += 1
        return {"E1VFVN30": 1.0} if i == 0 else ({"E1VFVN30": 0.0} if i == 1 else None)


class TestKhung(unittest.TestCase):
    def test_bao_toan_gia_tri_khi_khong_phi(self):
        """Không phí/thuế, không giao dịch: NAV cuối = tổng nạp nếu giá phẳng."""
        g = gia_gia_lap(); 
        for m in g: g[m][["Open", "High", "Low", "Close"]] = 10.0
        e = kb.Engine(g, tu="2020-01-01", nap_hang_thang=1e6)
        k = e.chay("trống", type("T", (), {"muc_tieu": lambda self, *a: None})())
        self.assertAlmostEqual(k.nav.iloc[-1], k.dong_gop.sum(), places=2)

    def test_t_cong_2_chan_ban_ngay(self):
        g = gia_gia_lap(); e = kb.Engine(g, tu="2020-01-01", nap_hang_thang=50e6)
        k = e.chay("t+2", MuaMotLan())
        self.assertGreaterEqual(k.so_lenh_bi_chan, 1)   # lệnh bán ở phiên sau lệnh mua bị chặn bởi T+2,5

    def test_phi_va_thue_duoc_tinh(self):
        g = gia_gia_lap(); e = kb.Engine(g, tu="2020-01-01", nap_hang_thang=50e6)
        k = e.chay("mua", type("M", (), {"muc_tieu": lambda self, eng, i, v, t, n: {"E1VFVN30": 1.0} if i == 0 else None})())
        self.assertGreater(k.chi_phi, 0)

    def test_tran_chan_mua(self):
        g = gia_gia_lap(); e = kb.Engine(g, tu="2020-01-01", nap_hang_thang=50e6)
        e.open["E1VFVN30"] = e.close["E1VFVN30"].shift(1) * 1.07   # mở cửa đúng giá trần
        k = e.chay("tran", type("M", (), {"muc_tieu": lambda self, eng, i, v, t, n: {"E1VFVN30": 1.0} if i < 3 else None})())
        self.assertGreaterEqual(k.so_lenh_bi_chan, 1)

    def test_khong_nhin_truoc_bctc(self):
        """Mọi kỳ BCTC TTM dùng tại ngày T phải có hiệu lực <= T."""
        d = "data/bctc"
        if not os.path.isdir(os.path.join(os.path.dirname(__file__), "..", d)): self.skipTest("không có dữ liệu")
        os.chdir(os.path.join(os.path.dirname(__file__), ".."))
        from tang2_ttm import DuLieuTTM
        dl = DuLieuTTM(); n = 0
        for ma in list(dl.ttm)[:40]:
            for t in pd.date_range("2021-01-01", "2026-01-01", freq="90D"):
                sn = dl.snapshots(ma, t) or []
                for s in sn: self.assertLessEqual(s["hl"], t); n += 1
        self.assertGreater(n, 0)

    def test_noi_bo_chi_dung_den_ngay_cong_bo(self):
        os.chdir(os.path.join(os.path.dirname(__file__), ".."))
        if not os.path.isdir("data/noibo"): self.skipTest("không có dữ liệu")
        from tang2_chon_ma import DuLieuCoBan
        dl = DuLieuCoBan()
        for ma in list(dl.noibo)[:30]:
            a = dl.ban_rong_noi_bo(ma, pd.Timestamp("2022-06-30"))
            muon = [(d, v) for d, v in dl.noibo[ma] if d > pd.Timestamp("2022-06-30")]
            b = sum(v for d, v in dl.noibo[ma] if pd.Timestamp("2021-06-30") < d <= pd.Timestamp("2022-06-30"))
            self.assertAlmostEqual(a, b)



class TestNhapModule(unittest.TestCase):
    """Mọi module trong v34 phải nhập được và không có tác dụng phụ (không tải dữ liệu khi nhập)."""
    def test_nhap_tat_ca(self):
        import importlib, glob
        goc = os.path.join(os.path.dirname(__file__), "..", "v34")
        for f in sorted(glob.glob(os.path.join(goc, "*.py"))):
            ten = os.path.basename(f)[:-3]
            if ten.startswith(("chay_", "kiem_thu", "tham_do", "chan_doan")): continue   # script chạy một lần, có thể có vòng chạy ở cấp module
            with self.subTest(module=ten):
                importlib.import_module(ten)



class TestDuLieuThuCong(unittest.TestCase):
    """Luồng nhập tay: ý kiến kiểm toán, cầm cố, lãi suất liên ngân hàng (dữ liệu giả)."""
    def setUp(self):
        import tempfile; self.d = tempfile.mkdtemp()
        from du_lieu_thu_cong import DuLieuThuCong
        self.cls = DuLieuThuCong

    def _ghi(self, ten, noi_dung):
        open(os.path.join(self.d, ten), "w").write(noi_dung)

    def test_khong_co_file_thi_khong_danh_gia(self):
        t = self.cls(self.d)
        self.assertIsNone(t.kiem_toan("AAA", pd.Timestamp("2025-06-01"))); self.assertIsNone(t.cam_co("AAA", pd.Timestamp("2025-06-01")))
        self.assertIsNone(t.tin_hieu_lai_suat(pd.bdate_range("2024-01-01", periods=50)))

    def test_y_kien_ngoai_tru_bi_loai(self):
        self._ghi("kiem_toan_y_kien.csv", "ma,nam,y_kien\nAAA,2023,chấp nhận toàn phần\nAAA,2024,ngoại trừ\nBBB,2024,chấp nhận toàn phần\n")
        t = self.cls(self.d)
        self.assertFalse(t.kiem_toan("AAA", pd.Timestamp("2025-06-01")))      # FY2024 mới nhất đã công bố, có ý kiến ngoại trừ
        self.assertTrue(t.kiem_toan("BBB", pd.Timestamp("2025-06-01")))
        self.assertIsNone(t.kiem_toan("CCC", pd.Timestamp("2025-06-01")))     # không có dữ liệu cho mã
        self.assertTrue(t.kiem_toan("AAA", pd.Timestamp("2025-02-01")))       # trước tháng 4: FY2024 chưa công bố, FY2023 sạch

    def test_cam_co_vuot_nguong(self):
        self._ghi("cam_co.csv", "ma,ngay,ty_le_pct\nAAA,2025-01-10,10\nAAA,2025-05-01,45\nBBB,2024-01-01,50\n")
        t = self.cls(self.d)
        self.assertFalse(t.cam_co("AAA", pd.Timestamp("2025-06-01")))         # mới nhất 45% >= 30%
        self.assertTrue(t.cam_co("AAA", pd.Timestamp("2025-03-01")))          # lúc đó mới nhất 10%
        self.assertIsNone(t.cam_co("BBB", pd.Timestamp("2025-06-01")))        # quá 12 tháng, không đánh giá

    def test_lai_suat_tang_manh_thi_tam_dung(self):
        ng = pd.date_range("2024-01-01", periods=60, freq="W"); gt = [1.0] * 30 + list(np.linspace(1.0, 3.5, 10)) + [3.5] * 20
        self._ghi("lai_suat_lnh.csv", "ngay,lai_suat_qua_dem_pct\n" + "\n".join(f"{d.date()},{v}" for d, v in zip(ng, gt)))
        t = self.cls(self.d); s = t.tin_hieu_lai_suat(pd.bdate_range("2024-01-01", "2025-02-28"))
        self.assertTrue(bool(s.iloc[10]))                                      # đầu kỳ lãi suất phẳng: được giải ngân
        self.assertFalse(bool(s.loc["2024-10-01":"2024-11-30"].all()))         # giai đoạn tăng mạnh: có lúc tạm dừng


if __name__ == "__main__":
    unittest.main()
