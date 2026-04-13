<script lang="ts">
	async function generateKeys(amount = 1) {
		generating = true;
		generateError = null;

		try {
			const res = await fetch(`/api/generate-key?n=${amount}`, {
				method: 'GET',
				headers: {
					accept: 'application/json'
				},
				credentials: 'include'
			});

			if (!res.ok) {
				const text = await res.text();
				throw new Error(text || `Request failed (${res.status})`);
			}

			const body = (await res.json()) as { access_keys?: string[] };
			if (!Array.isArray(body.access_keys)) throw new Error('Invalid response');

			keys = [...keys, ...body.access_keys];
		} catch (e) {
			generateError = e instanceof Error ? e.message : String(e);
		} finally {
			generating = false;
		}
	}

	let keys: string[] = $state([]);
	let generating = $state(false);
	let generateError: string | null = $state(null);
	let n = $state(1);
</script>

<div class="flex w-80 flex-col">
	<div class="mt-3 flex w-fit flex-row gap-1">
		<button type="button" onclick={() => generateKeys(n)} disabled={generating}>
			{generating ? 'Generating...' : `Generate keys`}
		</button>
		<input class="w-14" type="number" min="1" bind:value={n} />
	</div>
	<div class="space-around mt-3 flex flex-row">
		<ul class=" flex w-full flex-col items-start">
			{#if generateError}
				<p class="text-red-400">{generateError}</p>
			{/if}

			{#each keys as key}
				<li>
					{key}
				</li>
			{/each}
		</ul>
		{#if keys.length != 0}
			<button
				class="h-fit self-start"
				onclick={async () => {
					await navigator.clipboard.writeText(keys.join('\n'));
				}}>Copy</button
			>
		{/if}
	</div>
</div>
