/*
    SmartMart AI - Giai đoạn 1
    Thiết kế cơ sở dữ liệu SQL Server

    Lưu ý:
    - GroceryStoreDataset chỉ dùng cho nhận diện/tìm kiếm ảnh.
    - Không đưa giá bán, tồn kho hoặc hạn sử dụng giả định vào dataset.
    - Các thông tin kinh doanh phải được quản lý trong cơ sở dữ liệu này.
*/

IF DB_ID(N'SmartMartAI') IS NULL
BEGIN
    CREATE DATABASE SmartMartAI;
END;
GO

USE SmartMartAI;
GO

IF OBJECT_ID(N'dbo.DanhMuc', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.DanhMuc
    (
        MaDM INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_DanhMuc PRIMARY KEY,
        TenDM NVARCHAR(150) NOT NULL
            CONSTRAINT UQ_DanhMuc_TenDM UNIQUE,
        MoTa NVARCHAR(500) NULL,
        TrangThai BIT NOT NULL
            CONSTRAINT DF_DanhMuc_TrangThai DEFAULT (1)
    );
END;
GO

IF OBJECT_ID(N'dbo.SanPham', N'U') IS NULL
BEGIN
    CREATE TABLE dbo.SanPham
    (
        MaSP INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_SanPham PRIMARY KEY,
        MaDM INT NOT NULL,
        TenSP NVARCHAR(250) NOT NULL,
        MoTa NVARCHAR(1000) NULL,
        ThuongHieu NVARCHAR(150) NULL,
        Anh NVARCHAR(500) NULL,
        DonViTinh NVARCHAR(50) NOT NULL,
        GiaBan DECIMAL(18,2) NOT NULL,
        SoLuongTon INT NOT NULL
            CONSTRAINT DF_SanPham_SoLuongTon DEFAULT (0),
        HanSuDung DATE NULL,
        TrangThai BIT NOT NULL
            CONSTRAINT DF_SanPham_TrangThai DEFAULT (1),
        NgayTao DATETIME2(0) NOT NULL
            CONSTRAINT DF_SanPham_NgayTao DEFAULT (SYSDATETIME()),
        NgayCapNhat DATETIME2(0) NOT NULL
            CONSTRAINT DF_SanPham_NgayCapNhat DEFAULT (SYSDATETIME()),

        CONSTRAINT FK_SanPham_DanhMuc
            FOREIGN KEY (MaDM) REFERENCES dbo.DanhMuc(MaDM),
        CONSTRAINT CK_SanPham_GiaBan
            CHECK (GiaBan >= 0),
        CONSTRAINT CK_SanPham_SoLuongTon
            CHECK (SoLuongTon >= 0)
    );
END;
GO

IF OBJECT_ID(N'dbo.SanPhamAnh', N'U') IS NULL
BEGIN
    /*
        Bảng ánh xạ giữa sản phẩm trong SQL Server và ảnh/nhãn của
        GroceryStoreDataset. DuongDanAnhDataset không chứa giá hoặc tồn kho.
    */
    CREATE TABLE dbo.SanPhamAnh
    (
        MaAnh INT IDENTITY(1,1) NOT NULL
            CONSTRAINT PK_SanPhamAnh PRIMARY KEY,
        MaSP INT NOT NULL,
        DuongDanAnhDataset NVARCHAR(1000) NOT NULL,
        NhanDataset NVARCHAR(250) NOT NULL,
        LaAnhDaiDien BIT NOT NULL
            CONSTRAINT DF_SanPhamAnh_LaAnhDaiDien DEFAULT (0),
        TapDuLieu NVARCHAR(20) NOT NULL,
        NgayTao DATETIME2(0) NOT NULL
            CONSTRAINT DF_SanPhamAnh_NgayTao DEFAULT (SYSDATETIME()),

        CONSTRAINT FK_SanPhamAnh_SanPham
            FOREIGN KEY (MaSP) REFERENCES dbo.SanPham(MaSP),
        CONSTRAINT CK_SanPhamAnh_TapDuLieu
            CHECK (TapDuLieu IN (N'train', N'val', N'test'))
    );
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
              WHERE name = N'IX_SanPham_MaDM'
                AND object_id = OBJECT_ID(N'dbo.SanPham'))
BEGIN
    CREATE INDEX IX_SanPham_MaDM ON dbo.SanPham(MaDM);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
              WHERE name = N'IX_SanPham_TenSP'
                AND object_id = OBJECT_ID(N'dbo.SanPham'))
BEGIN
    CREATE INDEX IX_SanPham_TenSP ON dbo.SanPham(TenSP);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
              WHERE name = N'IX_SanPham_ThuongHieu'
                AND object_id = OBJECT_ID(N'dbo.SanPham'))
BEGIN
    CREATE INDEX IX_SanPham_ThuongHieu ON dbo.SanPham(ThuongHieu);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
              WHERE name = N'IX_SanPham_GiaBan_TrangThai'
                AND object_id = OBJECT_ID(N'dbo.SanPham'))
BEGIN
    CREATE INDEX IX_SanPham_GiaBan_TrangThai
        ON dbo.SanPham(GiaBan, TrangThai);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
              WHERE name = N'IX_SanPhamAnh_NhanDataset'
                AND object_id = OBJECT_ID(N'dbo.SanPhamAnh'))
BEGIN
    CREATE INDEX IX_SanPhamAnh_NhanDataset
        ON dbo.SanPhamAnh(NhanDataset);
END;
GO

IF NOT EXISTS (SELECT 1 FROM sys.indexes
              WHERE name = N'IX_SanPhamAnh_MaSP'
                AND object_id = OBJECT_ID(N'dbo.SanPhamAnh'))
BEGIN
    CREATE INDEX IX_SanPhamAnh_MaSP ON dbo.SanPhamAnh(MaSP);
END;
GO
