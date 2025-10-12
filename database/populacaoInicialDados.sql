
-- População inicial de dados complementares para o SGEA
-- Este script insere usuários, eventos, inscrições e certificados de exemplo.
-- Execute após criar o schema (por exemplo: sqlite3 db.sqlite3 < schema.sql && sqlite3 db.sqlite3 < populacaoInicialDados.sql)

BEGIN TRANSACTION;

-- Usuários (com perfis válidos: ADMIN, ORGANIZADOR, ALUNO, PROFESSOR)
INSERT INTO api_usuario (password, is_superuser, username, first_name, last_name, email, is_staff, is_active, nome, telefone, instituicao, perfil)
VALUES
	('pbkdf2_sha256$720000$org2$hashdemo', 0, 'org2', 'Lucas', 'Organiza', 'lucas@sgea.local', 0, 1, 'Lucas Organiza', '61955554444', NULL, 'ORGANIZADOR'),
	('pbkdf2_sha256$720000$aluno2$hashdemo', 0, 'aluno2', 'Mariana', 'Costa', 'mariana@sgea.local', 0, 1, 'Mariana Aluna', '61944443333', 'UFMG', 'ALUNO'),
	('pbkdf2_sha256$720000$prof2$hashdemo', 0, 'prof2', 'Rafael', 'Santos', 'rafael@sgea.local', 0, 1, 'Rafael Professor', '61933332222', 'UNICAMP', 'PROFESSOR');

-- Eventos (usar subqueries para obter organizador_id por username)
INSERT INTO api_evento (tipo, data_inicio, data_fim, local, capacidade, organizador_id)
VALUES
	('WORKSHOP', '2025-12-01', '2025-12-02', 'Sala 200', 40, (SELECT id FROM api_usuario WHERE username = 'org2')),
	('PALESTRA', '2025-10-20', '2025-10-20', 'Auditório Secundário', 150, (SELECT id FROM api_usuario WHERE username = 'org1')),
	('MINICURSO', '2025-11-12', '2025-11-13', 'Lab 202', 30, (SELECT id FROM api_usuario WHERE username = 'org2'));

-- Inscrições (evento_id e participante_id obtidos via subqueries; obedecer UNIQUE(evento_id, participante_id))
INSERT INTO api_inscricao (evento_id, participante_id, status, presenca_confirmada)
VALUES
	((SELECT id FROM api_evento WHERE tipo = 'WORKSHOP' AND local = 'Sala 200' LIMIT 1), (SELECT id FROM api_usuario WHERE username = 'aluno2' LIMIT 1), 'CONFIRMADA', 1),
	((SELECT id FROM api_evento WHERE tipo = 'PALESTRA' AND local = 'Auditório Secundário' LIMIT 1), (SELECT id FROM api_usuario WHERE username = 'prof2' LIMIT 1), 'PENDENTE', 0),
	((SELECT id FROM api_evento WHERE tipo = 'MINICURSO' AND local = 'Lab 202' LIMIT 1), (SELECT id FROM api_usuario WHERE username = 'aluno1' LIMIT 1), 'CONFIRMADA', 0);

-- Certificados (associar a uma inscrição existente e a um usuário emissor)
-- Usamos códigos UUID de exemplo (36 chars) e carga_horaria positiva.
INSERT INTO api_certificado (inscricao_id, emitido_por_id, codigo, carga_horaria, validade, observacoes)
VALUES
	(
		(SELECT i.id FROM api_inscricao i JOIN api_evento e ON i.evento_id = e.id WHERE e.local = 'Sala 200' AND i.participante_id = (SELECT id FROM api_usuario WHERE username = 'aluno2') LIMIT 1),
		(SELECT id FROM api_usuario WHERE username = 'org2' LIMIT 1),
		'c0a80100-0000-4000-8000-000000000001',
		8,
		'2026-12-01',
		'Participação completa no workshop.'
	),
	(
		(SELECT i.id FROM api_inscricao i JOIN api_evento e ON i.evento_id = e.id WHERE e.local = 'Lab 202' AND i.participante_id = (SELECT id FROM api_usuario WHERE username = 'aluno1') LIMIT 1),
		(SELECT id FROM api_usuario WHERE username = 'org2' LIMIT 1),
		'c0a80100-0000-4000-8000-000000000002',
		16,
		'2026-11-13',
		'Certificado de minicurso.'
	);

COMMIT;
