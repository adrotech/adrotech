import { defineCollection } from 'astro:content';
import { glob } from 'astro/loaders';
import { z } from 'astro/zod';

const sharedSchema = ({ image }: { image: any }) =>
	z.object({
		title: z.string(),
		description: z.string(),
		date: z.coerce.date(),
		updatedDate: z.coerce.date().optional(),
		tags: z.array(z.string()).default([]),
		category: z.string(),
		level: z.enum(['intro', 'intermedio', 'avanzado']).optional(),
		featured: z.boolean().default(false),
		heroImage: z.optional(image()),
	});

const cursos = defineCollection({
	loader: glob({ base: './src/content/cursos', pattern: '**/*.{md,mdx}' }),
	schema: sharedSchema,
});

const tutoriales = defineCollection({
	loader: glob({ base: './src/content/tutoriales', pattern: '**/*.{md,mdx}' }),
	schema: sharedSchema,
});

const posts = defineCollection({
	loader: glob({ base: './src/content/posts', pattern: '**/*.{md,mdx}' }),
	schema: sharedSchema,
});

export const collections = { cursos, tutoriales, posts };
