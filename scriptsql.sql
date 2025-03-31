-- DROP EXISTING OBJECTS
DROP TABLE IF EXISTS HistoricoCliente;
DROP TABLE IF EXISTS AlvoCliente;
DROP TABLE IF EXISTS RotaCliente;

-- CRIAÇÃO DAS TABELAS
CREATE TABLE AlvoCliente (
    ClienteID INT PRIMARY KEY,
    Nome VARCHAR(50),
    Email VARCHAR(50),
    DataCadastro DATETIME DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE RotaCliente (
    ClienteID INT PRIMARY KEY,
    Nome VARCHAR(50),
    Email VARCHAR(50)
);

CREATE TABLE HistoricoCliente (
    HistoricoID INTEGER PRIMARY KEY AUTOINCREMENT,
    ClienteID INT,
    Nome_Antigo VARCHAR(50),
    Email_Antigo VARCHAR(50),
    Nome_Novo VARCHAR(50),
    Email_Novo VARCHAR(50),
    DataAlteracao DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Inserindo (20+ linhas) na tabela de destino
INSERT INTO AlvoCliente (ClienteID, Nome, Email)
VALUES 
  (1, 'Ana Silva', 'ana.silva@mail.com'),
  (2, 'Bruno Costa', 'bruno.costa@mail.com'),
  (3, 'Carlos Souza', 'carlos.souza@mail.com'),
  (4, 'Daniel Pereira', 'daniel.pereira@mail.com'),
  (5, 'Eduarda Lima', 'eduarda.lima@mail.com'),
  (6, 'Fernando Rocha', 'fernando.rocha@mail.com'),
  (7, 'Gabriela Alves', 'gabriela.alves@mail.com'),
  (8, 'Helena Martins', 'helena.martins@mail.com'),
  (9, 'Igor Fernandes', 'igor.fernandes@mail.com'),
  (10, 'Joana Dias', 'joana.dias@mail.com'),
  (11, 'Kaio Mendes', 'kaio.mendes@mail.com'),
  (12, 'Lara Gomes', 'lara.gomes@mail.com'),
  (13, 'Marcos Teixeira', 'marcos.teixeira@mail.com'),
  (14, 'Nina Barros', 'nina.barros@mail.com'),
  (15, 'Otavio Ribeiro', 'otavio.ribeiro@mail.com'),
  (16, 'Paula Cardoso', 'paula.cardoso@mail.com'),
  (17, 'Quentin Souza', 'quentin.souza@mail.com'),
  (18, 'Rafaela Pinto', 'rafaela.pinto@mail.com'),
  (19, 'Samuel Araújo', 'samuel.araujo@mail.com'),
  (20, 'Teresa Castro', 'teresa.castro@mail.com');

-- Inserindo (10+ linhas) na tabela fonte, com dados para atualização e inclusão
-- Algumas IDs são iguais para atualização; outras são novas para inclusão.
INSERT INTO RotaCliente (ClienteID, Nome, Email)
VALUES 
  (3, 'Carlos Souza', 'carlos.novo@mail.com'),      -- atualização (alteração de email)
  (5, 'Eduarda Lima', 'eduarda.lima@mail.com'),        -- igual: sem alteração
  (7, 'Gabriela Alves', 'gabriela.alterada@mail.com'), -- atualização
  (10, 'Joana Dias', 'joana.dias@mail.com'),           -- igual
  (14, 'Nina Barros', 'nina.atual@mail.com'),          -- atualização
  (17, 'Quentin Souza', 'quentin.novo@mail.com'),      -- atualização
  (21, 'Ulisses Nunes', 'ulisses.nunes@mail.com'),     -- inserção
  (22, 'Vicente Ramos', 'vicente.ramos@mail.com'),     -- inserção
  (23, 'Wagner Lopes', 'wagner.lopes@mail.com'),       -- inserção
  (24, 'Xavier Silva', 'xavier.silva@mail.com');       -- inserção

-- CRIAÇÃO DA TRIGGER: Grava histórico após atualização na tabela AlvoCliente
CREATE TRIGGER trgAfterUpdateClientes
AFTER UPDATE ON AlvoCliente
FOR EACH ROW
BEGIN
    INSERT INTO HistoricoCliente (ClienteID, Nome_Antigo, Email_Antigo, Nome_Novo, Email_Novo, DataAlteracao)
    VALUES (OLD.ClienteID, OLD.Nome, OLD.Email, NEW.Nome, NEW.Email, CURRENT_TIMESTAMP);
END;

-- SIMULAÇÃO DA OPERAÇÃO MERGE:
-- 1. Atualização de linhas existentes com dados diferentes
UPDATE AlvoCliente
SET Nome = (SELECT s.Nome FROM RotaCliente s WHERE s.ClienteID = AlvoCliente.ClienteID),
    Email = (SELECT s.Email FROM RotaCliente s WHERE s.ClienteID = AlvoCliente.ClienteID)
WHERE ClienteID IN (SELECT ClienteID FROM RotaCliente)
  AND (Nome <> (SELECT s.Nome FROM RotaCliente s WHERE s.ClienteID = AlvoCliente.ClienteID)
       OR Email <> (SELECT s.Email FROM RotaCliente s WHERE s.ClienteID = AlvoCliente.ClienteID));

-- 2. Inserção de novas linhas que não existem na tabela de destino
INSERT INTO AlvoCliente (ClienteID, Nome, Email)
SELECT ClienteID, Nome, Email FROM RotaCliente
WHERE ClienteID NOT IN (SELECT ClienteID FROM AlvoCliente);

-- 3. Remoção de linhas da tabela de destino ausentes da tabela fonte
DELETE FROM AlvoCliente
WHERE ClienteID NOT IN (SELECT ClienteID FROM RotaCliente);

-- APRESENTAÇÃO DOS RESULTADOS
SELECT * FROM AlvoCliente;
SELECT * FROM RotaCliente;
SELECT * FROM HistoricoCliente;