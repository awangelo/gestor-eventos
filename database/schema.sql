-- Script de criação e população inicial do banco de dados do Sistema de Gestão de Eventos Acadêmicos (SGEA)
-- Banco alvo: SQLite 3

PRAGMA foreign_keys = OFF;

DROP TRIGGER IF EXISTS trg_api_evento_update;
DROP TRIGGER IF EXISTS trg_api_inscricao_update;
DROP TRIGGER IF EXISTS trg_api_certificado_insert;

DROP TABLE IF EXISTS api_certificado;
DROP TABLE IF EXISTS api_inscricao;
DROP TABLE IF EXISTS api_evento;
DROP TABLE IF EXISTS api_usuario;

PRAGMA foreign_keys = ON;

-- Tabela de usuários customizada a partir de django.contrib.auth.models.AbstractUser
CREATE TABLE api_usuario (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    password VARCHAR(128) NOT NULL,
    last_login DATETIME NULL,
    is_superuser BOOLEAN NOT NULL DEFAULT 0,
    username VARCHAR(150) NOT NULL UNIQUE,
    first_name VARCHAR(150) NOT NULL DEFAULT '',
    last_name VARCHAR(150) NOT NULL DEFAULT '',
    email VARCHAR(254) NOT NULL DEFAULT '',
    is_staff BOOLEAN NOT NULL DEFAULT 0,
    is_active BOOLEAN NOT NULL DEFAULT 1,
    date_joined DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    nome VARCHAR(120) NOT NULL,
    telefone VARCHAR(20) NOT NULL,
    instituicao VARCHAR(20),
    perfil VARCHAR(20) NOT NULL,
    CHECK (perfil IN ('ALUNO', 'PROFESSOR', 'ORGANIZADOR', 'ADMIN')),
    CHECK (
        (perfil IN ('ALUNO', 'PROFESSOR') AND instituicao IS NOT NULL AND instituicao <> '')
        OR perfil IN ('ORGANIZADOR', 'ADMIN')
    )
);

CREATE INDEX api_usuario_perfil_idx ON api_usuario (perfil);

CREATE TABLE api_evento (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    tipo VARCHAR(20) NOT NULL,
    data_inicio DATE NOT NULL,
    data_fim DATE NOT NULL,
    local VARCHAR(150) NOT NULL,
    capacidade INTEGER NOT NULL CHECK (capacidade > 0),
    organizador_id INTEGER NOT NULL,
    criado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    CHECK (tipo IN ('PALESTRA', 'WORKSHOP', 'MINICURSO', 'SEMINARIO', 'OUTRO')),
    CHECK (data_fim >= data_inicio),
    FOREIGN KEY (organizador_id) REFERENCES api_usuario (id) ON DELETE RESTRICT
);

CREATE INDEX api_evento_tipo_idx ON api_evento (tipo);
CREATE INDEX api_evento_data_inicio_idx ON api_evento (data_inicio);
CREATE INDEX api_evento_organizador_idx ON api_evento (organizador_id);

CREATE TRIGGER trg_api_evento_update
AFTER UPDATE ON api_evento
FOR EACH ROW
BEGIN
    UPDATE api_evento SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TABLE api_inscricao (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    evento_id INTEGER NOT NULL,
    participante_id INTEGER NOT NULL,
    status VARCHAR(15) NOT NULL DEFAULT 'PENDENTE',
    data_inscricao DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    atualizado_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    presenca_confirmada BOOLEAN NOT NULL DEFAULT 0,
    CHECK (status IN ('PENDENTE', 'CONFIRMADA', 'CANCELADA')),
    CHECK ((presenca_confirmada = 0) OR status = 'CONFIRMADA'),
    UNIQUE (evento_id, participante_id),
    FOREIGN KEY (evento_id) REFERENCES api_evento (id) ON DELETE CASCADE,
    FOREIGN KEY (participante_id) REFERENCES api_usuario (id) ON DELETE CASCADE
);

CREATE INDEX api_inscricao_evento_status_idx ON api_inscricao (evento_id, status);
CREATE INDEX api_inscricao_participante_idx ON api_inscricao (participante_id);

CREATE TRIGGER trg_api_inscricao_update
AFTER UPDATE ON api_inscricao
FOR EACH ROW
BEGIN
    UPDATE api_inscricao SET atualizado_em = CURRENT_TIMESTAMP WHERE id = NEW.id;
END;

CREATE TABLE api_certificado (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    inscricao_id INTEGER NOT NULL UNIQUE,
    emitido_por_id INTEGER NOT NULL,
    codigo CHAR(36) NOT NULL UNIQUE,
    carga_horaria INTEGER NOT NULL CHECK (carga_horaria > 0),
    emitido_em DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP,
    validade DATE,
    observacoes TEXT,
    FOREIGN KEY (inscricao_id) REFERENCES api_inscricao (id) ON DELETE CASCADE,
    FOREIGN KEY (emitido_por_id) REFERENCES api_usuario (id) ON DELETE RESTRICT
);

CREATE INDEX api_certificado_emitente_idx ON api_certificado (emitido_por_id);
CREATE INDEX api_certificado_codigo_idx ON api_certificado (codigo);

CREATE TRIGGER trg_api_certificado_insert
AFTER INSERT ON api_certificado
FOR EACH ROW
BEGIN
    UPDATE api_certificado
    SET codigo = CASE
        WHEN NEW.codigo IS NULL OR NEW.codigo = '' THEN LOWER(HEX(RANDOMBLOB(16)))
        ELSE NEW.codigo
    END
    WHERE id = NEW.id;
END;

-- Perfil de acesso inicial
INSERT INTO api_usuario (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, nome, telefone, instituicao, perfil)
VALUES
    ('pbkdf2_sha256$720000$admin$hashdemo', 1, 'admin', 'Admin', 'Geral', 'admin@sgea.local', 1, 1, 'Administrador Geral', '61999990000', NULL, 'ADMIN'),
    ('pbkdf2_sha256$720000$organizador$hashdemo', 0, 'org1', 'Ana', 'Eventos', 'ana@sgea.local', 0, 1, 'Ana Organiza', '61988887777', NULL, 'ORGANIZADOR'),
    ('pbkdf2_sha256$720000$aluno$hashdemo', 0, 'aluno1', 'Bruno', 'Silva', 'bruno@sgea.local', 0, 1, 'Bruno Aluno', '61977776666', 'UNB', 'ALUNO'),
    ('pbkdf2_sha256$720000$prof$hashdemo', 0, 'prof1', 'Carla', 'Oliveira', 'carla@sgea.local', 0, 1, 'Carla Professora', '61966665555', 'IFB', 'PROFESSOR');

INSERT INTO api_evento (tipo, data_inicio, data_fim, local, capacidade, organizador_id)
VALUES
    ('PALESTRA', '2025-11-10', '2025-11-10', 'Auditorio Central', 100, 2),
    ('MINICURSO', '2025-11-12', '2025-11-14', 'Lab 101', 25, 2);

INSERT INTO api_inscricao (evento_id, participante_id, status, presenca_confirmada)
VALUES
    (1, 3, 'CONFIRMADA', 1),
    (1, 4, 'PENDENTE', 0),
    (2, 3, 'CONFIRMADA', 0);

INSERT INTO api_certificado (inscricao_id, emitido_por_id, codigo, carga_horaria, validade, observacoes)
VALUES
    (1, 2, 'sgea-ab12-xy98-2025', 4, '2026-11-10', 'Participacao integral na palestra inaugural.');
