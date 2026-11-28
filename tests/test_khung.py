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



class TestChatLuongDuLieu(unittest.TestCase):
    """Dữ liệu trong repo phải nạp được và hợp lý (bắt bản ghi rác của nguồn)."""
    def setUp(self):
        goc = os.path.join(os.path.dirname(__file__), "..")
        os.chdir(goc)
        if not os.path.isdir("data/cafef") or not os.path.isdir("data/bctc"): self.skipTest("không có dữ liệu")

    def test_nap_bo_du_lieu_dai(self):
        from du_lieu_dai import DuLieuDai
        dl = DuLieuDai()
        self.assertGreater(len(dl.nam), 100)
        for ma, ds in dl.nam.items():
            for y in ds: self.assertTrue(1990 <= y <= 2100, f"{ma} năm {y}")

    def test_gia_hop_le(self):
        import glob
        n = 0
        for f in glob.glob("data/gia_dai/[A-Z]*.csv.gz")[:80]:
            df = pd.read_csv(f, parse_dates=["Date"])
            self.assertTrue((df.Close > 0).all(), f); self.assertTrue(df.Date.is_monotonic_increasing, f); self.assertFalse(df.Date.duplicated().any(), f); n += 1
        self.assertGreater(n, 10)

    def test_bctc_cau_truc(self):
        import glob, json
        for f in glob.glob("data/bctc/[A-Z]*.json")[:100]:
            d = json.load(open(f))
            self.assertIn("kqkd", d, f)



class TestBaoCao(unittest.TestCase):
    """Chỉ báo tầng 3 và so sánh thay đổi của báo cáo hằng ngày (dữ liệu giả)."""
    def _gia(self, xu_huong):
        ng = pd.bdate_range("2024-01-01", periods=320)
        vn = np.concatenate([np.linspace(1000, 1500, 220), np.linspace(1500, 1500 * (1.1 if xu_huong == "len" else 0.8), 100)])
        mk = lambda c: pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c, "Volume": np.full(len(c), 1e6)}, index=ng)
        g = {"VNINDEX": mk(vn)}
        for i in range(10): g[f"M{i}"] = mk(vn * (1 + 0.01 * i))
        return g

    def test_chi_bao_xuong_duoi_ma200(self):
        import bao_cao_v34 as bc
        g = self._gia("xuong"); t = bc.chi_bao_tang3(g, [f"M{i}" for i in range(10)])
        self.assertFalse(t["tren_ma200"]); self.assertLess(t["cach_ma200_pct"], 0)
        self.assertEqual(t["do_rong_so_ma"], 10); self.assertLess(t["do_rong_ma200_pct"], 50)
        self.assertLess(t["cach_dinh_52t_pct"], 0); self.assertGreaterEqual(t["so_phien_cung_phia"], 1)

    def test_chi_bao_len_tren_ma200(self):
        import bao_cao_v34 as bc
        t = bc.chi_bao_tang3(self._gia("len"), [f"M{i}" for i in range(10)])
        self.assertTrue(t["tren_ma200"]); self.assertGreater(t["do_rong_ma200_pct"], 50)

    def test_so_sanh_thay_doi(self):
        import bao_cao_v34 as bc
        sl = {"tang3": {"tren_ma200": False}, "tat_ca_dat_loc": ["AAA", "CCC"], "bctc_cham": [{"ma": "ZZZ"}], "bctc_moi_7_ngay": [{"ma": "YYY"}]}
        cu = {"tren_ma200": True, "tat_ca_dat_loc": ["AAA", "BBB"], "bctc_cham": [], "bctc_moi": []}
        thay, lan_dau = bc.so_sanh_trang_thai(cu, sl)
        self.assertFalse(lan_dau); chuoi = " ".join(thay)
        for tu in ("MA200 đổi", "CCC", "BBB", "ZZZ", "YYY"): self.assertIn(tu, chuoi)
        self.assertEqual(bc.so_sanh_trang_thai(None, sl), ([], True))                  # lần đầu: không có so sánh
        self.assertEqual(bc.so_sanh_trang_thai({"tren_ma200": False, "tat_ca_dat_loc": ["AAA", "CCC"], "bctc_cham": ["ZZZ"], "bctc_moi": ["YYY"]}, sl)[0], [])   # không đổi

    def test_dung_markdown_day_du_cac_tang(self):
        import bao_cao_v34 as bc
        sl = {"ngay_du_lieu": "2026-11-27", "tang3": {"vnindex": 1, "ma200": 2, "tren_ma200": False, "cach_ma200_pct": -1.0, "so_phien_cung_phia": 3, "do_rong_ma200_pct": 10.0, "do_rong_ma50_pct": 20.0, "do_rong_so_ma": 5,
              "bien_dong_20p_pct": 18.0, "bien_dong_ty_le": 1.1, "cach_dinh_52t_pct": -5.0, "gd_ty_le": 1.0, "hung_phan": False, "nong_so_ma": 0, "nong_pct": 0.0}, "so_ma_dat_loc": 1, "so_ma_thanh_khoan": 5, "danh_sach_chat_luong": [{"ma": "AAA", "nganh": "X", "diem": 0.5, "roe_tb": 10.0, "co_tuc_tien_5nam": 4, "dat": 6, "danh_gia": 6, "tang_3t": 5.0, "tang_12t": 20.0, "nong": False}],
              "gia_moi": 1, "gia_cu": 0, "so_ma_theo_doi": 5, "vi_the": None}
        md = bc.dung_markdown(sl, None, [], False, "https://x", "https://huongdan")
        for muc in ("## Tóm tắt nhanh", "https://huongdan", "Cách hiểu", "## 0.", "## 1. Tầng 3", "## 2. Tầng 1", "## 3. Tầng 2", "## 4. Dữ liệu", "## 5. Lời bình", "## 6. Tình trạng các tầng", "https://x", "AAA"): self.assertIn(muc, md)



class TestNhanGiaiNghia(unittest.TestCase):
    def test_nhan(self):
        import bao_cao_v34 as bc
        self.assertEqual(bc.nhan_do_rong(10), "yếu"); self.assertEqual(bc.nhan_do_rong(45), "trung bình"); self.assertEqual(bc.nhan_do_rong(80), "mạnh")
        self.assertEqual(bc.nhan_bien_dong(1.1), "bình thường"); self.assertEqual(bc.nhan_bien_dong(1.6), "cao"); self.assertEqual(bc.nhan_bien_dong(2.5), "rất cao")
        self.assertEqual(bc.nhan_cach_dinh(-2), "gần đỉnh"); self.assertEqual(bc.nhan_cach_dinh(-10), "điều chỉnh vừa"); self.assertEqual(bc.nhan_cach_dinh(-20), "giảm sâu"); self.assertEqual(bc.nhan_cach_dinh(-40), "giảm rất sâu")

    def test_tom_tat_theo_tin_hieu(self):
        import bao_cao_v34 as bc
        t3 = {"tren_ma200": True, "do_rong_ma200_pct": 70.0, "bien_dong_ty_le": 1.0}
        self.assertIn("Mua đều E1VFVN30 như bình thường", " ".join(bc.tom_tat_nhanh({"tang3": t3, "bctc_cham": []}, [], False)))
        t3["tren_ma200"] = False
        self.assertIn("Tạm dừng mua thêm", " ".join(bc.tom_tat_nhanh({"tang3": t3, "bctc_cham": [{"ma": "A"}]}, ["x"], False)))



class TestChiBaoNong(unittest.TestCase):
    def test_tang_gan_va_la_nong(self):
        import bao_cao_v34 as bc
        c = pd.Series(np.linspace(100, 100, 300)); self.assertFalse(bc.la_nong(c))
        c2 = pd.Series(np.r_[np.full(237, 100.0), np.linspace(100, 140, 63)]); self.assertTrue(bc.la_nong(c2))          # tăng 40% trong 63 phiên
        c3 = pd.Series(np.linspace(100, 300, 300)); self.assertTrue(bc.la_nong(c3))                                      # tăng > 100% trong 250 phiên
        self.assertTrue(np.isnan(bc.tang_gan(pd.Series([1.0, 2.0]), 63)))

    def test_hung_phan_khi_giao_dich_va_gia_deu_cao(self):
        import bao_cao_v34 as bc
        ng = pd.bdate_range("2023-01-01", periods=330)
        vn = np.concatenate([np.full(200, 1000.0), np.linspace(1000, 1300, 130)])          # kéo xa MA200
        vol = np.concatenate([np.full(300, 1e6), np.full(30, 3e6)])                        # giao dịch bùng nổ 30 phiên cuối
        mk = lambda c, v: pd.DataFrame({"Open": c, "High": c, "Low": c, "Close": c, "Volume": v}, index=ng)
        t = bc.chi_bao_tang3({"VNINDEX": mk(vn, vol)}, [])
        self.assertGreaterEqual(t["gd_ty_le"], 1.5); self.assertGreaterEqual(t["cach_ma200_pct"], 10); self.assertTrue(t["hung_phan"])
        yen = bc.chi_bao_tang3({"VNINDEX": mk(vn, np.full(330, 1e6))}, [])
        self.assertFalse(yen["hung_phan"])

    def test_nhan_moi(self):
        import bao_cao_v34 as bc
        self.assertEqual(bc.nhan_gd(1.0), "bình thường"); self.assertEqual(bc.nhan_gd(1.5), "sôi động"); self.assertEqual(bc.nhan_gd(2.5), "rất sôi động")
        self.assertEqual(bc.nhan_nong(5), "ít"); self.assertEqual(bc.nhan_nong(15), "nhiều"); self.assertEqual(bc.nhan_nong(40), "rất nhiều")


if __name__ == "__main__":
    unittest.main()
