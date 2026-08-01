# Estratégias de busca — PRISMA-S

## Registro obrigatório

Para cada busca preservar:

- base e plataforma;
- data;
- período coberto;
- estratégia exatamente executada;
- filtros;
- número retornado;
- formato exportado;
- método de deduplicação;
- atualização;
- busca por referências e citações;
- uso de IA.

As estratégias abaixo são protótipos PubMed. Devem ser traduzidas para cada base e revisadas pelo PRESS antes de serem consideradas finais.

## População comum

```text
("Child, Preschool"[Mesh] OR preschool*[tiab] OR pre-school*[tiab]
 OR "early childhood"[tiab] OR kindergarten*[tiab]
 OR "young child*"[tiab])
```

## Módulo A — Cuidado responsivo

```text
(população)
AND
("responsive caregiv*"[tiab] OR "responsive parent*"[tiab]
 OR "parent-child interaction"[tiab] OR scaffolding[tiab]
 OR "guided play"[tiab] OR "home learning environment"[tiab]
 OR "parent coaching"[tiab] OR "parent-mediated"[tiab])
AND
(random*[tiab] OR trial[tiab] OR intervention*[tiab]
 OR longitudinal[tiab] OR cohort[tiab] OR systematic[sb])
```

## Módulo B — Linguagem e alfabetização emergente

```text
(população)
AND
("shared book reading"[tiab] OR "dialogic reading"[tiab]
 OR storybook*[tiab] OR "print referencing"[tiab]
 OR "oral language"[tiab] OR vocabulary[tiab]
 OR pragmatic*[tiab] OR narrative*[tiab]
 OR "emergent literacy"[tiab] OR "phonological awareness"[tiab]
 OR alphabet*[tiab] OR "letter knowledge"[tiab])
AND
(parent*[tiab] OR caregiver*[tiab] OR teacher*[tiab]
 OR home[tiab] OR preschool[tiab])
```

## Módulo C — Atenção e funções executivas

```text
(população)
AND
("Executive Function"[Mesh] OR executive function*[tiab]
 OR attention[tiab] OR inhibition[tiab]
 OR "working memory"[tiab] OR "cognitive flexibility"[tiab]
 OR "task switching"[tiab] OR planning[tiab]
 OR persistence[tiab] OR "delay tolerance"[tiab]
 OR "emotion regulation"[tiab] OR self-regulation[tiab]
 OR reinforcement[tiab] OR motivation[tiab])
AND
(intervention*[tiab] OR training[tiab] OR trial[tiab]
 OR longitudinal[tiab] OR systematic[sb])
```

## Módulo D — Brincadeira, memória, motricidade e numeracia

```text
(população)
AND
("guided play"[tiab] OR pretend play[tiab] OR symbolic play[tiab]
 OR imitation[tiab] OR demonstration[tiab]
 OR problem solving[tiab] OR memory[tiab] OR retention[tiab]
 OR transfer[tiab] OR generalization[tiab]
 OR fine motor[tiab] OR visual motor[tiab]
 OR embodied learning[tiab] OR numeracy[tiab]
 OR mathematics[tiab] OR counting[tiab] OR spatial language[tiab])
```

## Módulo E — Sono, respiração, telas e sensorial

```text
(população)
AND
(sleep[tiab] OR "sleep duration"[tiab] OR "sleep timing"[tiab]
 OR "sleep quality"[tiab] OR "daytime sleepiness"[tiab]
 OR snoring[tiab] OR "sleep disordered breathing"[tiab]
 OR "obstructive sleep apnea"[tiab] OR rhinitis[tiab]
 OR asthma[tiab] OR screen*[tiab] OR television[tiab]
 OR tablet*[tiab] OR sensory[tiab] OR noise[tiab]
 OR "visual clutter"[tiab])
AND
(attention[tiab] OR cognition[tiab] OR language[tiab]
 OR behavior*[tiab] OR learning[tiab]
 OR executive[tiab] OR regulation[tiab] OR development*[tiab])
```

## Módulo F — Informantes e contexto familiar

```text
(população)
AND
("multi-informant"[tiab] OR informant*[tiab]
 OR "parent report"[tiab] OR "teacher report"[tiab]
 OR discrepancy[tiab] OR agreement[tiab]
 OR "parenting stress"[tiab] OR burden[tiab]
 OR co-regulation[tiab] OR coparent*[tiab]
 OR separation[tiab] OR divorce[tiab]
 OR "shared care"[tiab] OR transition*[tiab]
 OR "trauma-informed"[tiab])
AND
(observ*[tiab] OR assess*[tiab] OR behavior*[tiab]
 OR adjustment[tiab] OR regulation[tiab] OR development*[tiab])
```

## Regras adicionais

- não depender apenas de filtro automático de idade;
- preservar exportações originais por base;
- registrar literatura cinzenta e busca por citações;
- documentar toda expansão, redução ou correção da estratégia;
- registrar explicitamente qualquer uso de IA na recuperação ou classificação.